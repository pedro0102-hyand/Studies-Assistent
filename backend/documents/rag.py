"""
Etapa 5+ — RAG: embedding da pergunta e (mais tarde) retrieval + LLM.
"""
from __future__ import annotations

from typing import Any

from django.conf import settings

from . import ollama_chat
from . import ollama_embed
from .ollama_chat import OllamaChatError
from .ollama_embed import OllamaEmbedError

_CONTEXT_SEPARATOR = '\n\n---\n\n'


def build_context_from_chunks(
    chunks: list[dict[str, Any]],
    *,
    max_chars: int | None = None,
    label_sources: bool = True,
    excerpt_limit: int = 800,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Etapa 5.4 — junta os textos dos chunks recuperados até `RAG_MAX_CONTEXT_CHARS`.

    - `label_sources`: prefixa cada bloco com ``[fonte: nome, chunk i]`` para transparência.
    - Devolve ``(contexto_para_llm, sources)`` onde ``sources`` segue o contrato RagSource
      (document_id, chunk_index, original_name, excerpt).
    """
    if max_chars is not None:
        limit = max(int(max_chars), 1)
    else:
        limit = max(
            int(getattr(settings, 'RAG_MAX_CONTEXT_CHARS', 12000)),
            200,
        )

    parts: list[str] = []
    sources: list[dict[str, Any]] = []
    used = 0

    for item in chunks:
        raw = item.get('document')
        text = (raw or '').strip()
        meta = item.get('metadata') or {}
        try:
            doc_id = int(meta.get('document_id') or 0)
        except (TypeError, ValueError):
            doc_id = 0
        try:
            chunk_idx = int(meta.get('chunk_index') or 0)
        except (TypeError, ValueError):
            chunk_idx = 0
        orig = str(meta.get('original_name') or '')[:200]

        header = (
            f'[fonte: {orig}, chunk {chunk_idx}]\n' if label_sources else ''
        )

        sep_len = len(_CONTEXT_SEPARATOR) if parts else 0
        room = limit - used - sep_len
        if room <= 0:
            break
        if len(header) > room:
            break

        body_budget = room - len(header)
        if body_budget <= 0:
            break

        if len(text) <= body_budget:
            body = text
            truncated = False
        else:
            if body_budget <= 1:
                break
            body = text[: body_budget - 1] + '…'
            truncated = True

        block = header + body
        if parts:
            parts.append(_CONTEXT_SEPARATOR)
        parts.append(block)
        used += sep_len + len(block)

        ex = body if len(body) <= excerpt_limit else body[: excerpt_limit - 1] + '…'
        sources.append(
            {
                'document_id': doc_id,
                'chunk_index': chunk_idx,
                'original_name': orig,
                'excerpt': ex,
            }
        )

        if truncated:
            break

    return (''.join(parts), sources)


def generate_rag_answer(
    context: str,
    question: str,
    *,
    system_prompt: str | None = None,
) -> str:
    """
    Etapa 5.5 — gera a resposta com o modelo de chat do Ollama (``OLLAMA_CHAT_*``).

    System: instruções de fidelidade ao contexto (``RAG_SYSTEM_PROMPT`` ou override).
    User: bloco com contexto recuperado + pergunta.
    """
    q = (question or '').strip()
    if not q:
        raise ValueError('A pergunta não pode ser vazia.')

    sys_text = (system_prompt or '').strip() or getattr(
        settings,
        'RAG_SYSTEM_PROMPT',
        'Responde só com base no contexto fornecido.',
    )
    ctx = (context or '').strip()
    user_block = (
        'Utiliza apenas o seguinte contexto fornecido (trechos dos PDFs do utilizador e anexos enviados no chat).\n\n'
        f'---\n{ctx if ctx else "(Nenhum trecho relevante foi encontrado.)"}\n---\n\n'
        f'Pergunta: {q}'
    )

    try:
        return ollama_chat.ollama_chat_completion(
            [
                {'role': 'system', 'content': sys_text},
                {'role': 'user', 'content': user_block},
            ],
            base_url=getattr(settings, 'OLLAMA_BASE_URL', 'http://127.0.0.1:11434'),
            model=getattr(settings, 'OLLAMA_CHAT_MODEL', 'gemma2:2b'),
            timeout=float(getattr(settings, 'OLLAMA_CHAT_TIMEOUT', 180)),
        )
    except OllamaChatError as exc:
        raise OllamaChatError(
            'Não foi possível gerar a resposta com o modelo de chat. '
            f'Confirma que o Ollama está a correr e que o modelo existe '
            f'(ex.: ollama pull {getattr(settings, "OLLAMA_CHAT_MODEL", "gemma2:2b")}). '
            f'Detalhe: {exc}'
        ) from exc


def embed_question(text: str) -> list[float]:
    """
    Gera o vetor da pergunta com as mesmas settings dos PDFs (OLLAMA_EMBED_*).
    Erros de rede/Ollama vêm como OllamaEmbedError com mensagem utilizável.
    """
    try:
        return ollama_embed.embed_query(
            (text or '').strip(),
            base_url=getattr(settings, 'OLLAMA_BASE_URL', 'http://127.0.0.1:11434'),
            model=getattr(settings, 'OLLAMA_EMBED_MODEL', 'nomic-embed-text:latest'),
            timeout=float(getattr(settings, 'OLLAMA_EMBED_TIMEOUT', 120)),
            batch_size=1,
        )
    except OllamaEmbedError as exc:
        raise OllamaEmbedError(
            'Não foi possível obter o embedding da pergunta. '
            'Confirma que o Ollama está a correr e que o modelo de embeddings existe '
            f'(ex.: ollama pull {getattr(settings, "OLLAMA_EMBED_MODEL", "nomic-embed-text")}). '
            f'Detalhe: {exc}'
        ) from exc


def run_rag_for_user(
    *,
    user_id: int,
    question: str,
    document_ids: list[int] | None,
    attachment_context: str | None = None,
    attachment_filename: str | None = None,
) -> dict[str, Any]:
    """
    Etapa 5.6 — pipeline completo: embedding → Chroma (sempre com filtro user_id) →
    contexto → resposta LLM. ``document_ids`` já deve estar validado em relação ao utilizador.

    ``attachment_context``: texto extraído de um PDF anexado à mensagem; junta-se ao contexto
    enviado ao LLM (não entra no embedding da pergunta).
    """
    from .chroma_index import search_similar_chunks

    top_k = int(getattr(settings, 'RAG_TOP_K', 5))
    embedding = embed_question(question)

    # Quando o utilizador não restringe `document_ids`, é comum o top_k vir todo do mesmo PDF.
    # Pedimos mais candidatos e depois diversificamos por documento.
    diversified = (
        document_ids is None
        and bool(getattr(settings, 'RAG_DIVERSIFY_RESULTS', True))
    )
    request_k = min(50, max(1, top_k * (5 if diversified else 1)))

    chunks = search_similar_chunks(
        embedding,
        user_id=user_id,
        top_k=request_k,
        document_ids=document_ids,
    )

    if diversified and chunks:
        per_doc = int(getattr(settings, 'RAG_MAX_CHUNKS_PER_DOCUMENT', 2))
        per_doc = max(1, min(10, per_doc))
        counts: dict[int, int] = {}
        diversified_chunks: list[dict[str, Any]] = []
        for item in chunks:
            meta = item.get('metadata') or {}
            try:
                doc_id = int(meta.get('document_id') or 0)
            except (TypeError, ValueError):
                doc_id = 0
            if doc_id > 0:
                used = counts.get(doc_id, 0)
                if used >= per_doc:
                    continue
                counts[doc_id] = used + 1
            diversified_chunks.append(item)
            if len(diversified_chunks) >= top_k:
                break
        chunks = diversified_chunks

    context, sources = build_context_from_chunks(chunks)

    att = (attachment_context or '').strip()
    if att:
        max_ctx = max(500, int(getattr(settings, 'RAG_MAX_CONTEXT_CHARS', 12000)))
        block = '\n\n--- Texto extraído do PDF anexado à mensagem ---\n' + f'{att}'
        if len(context) + len(block) > max_ctx:
            room = max(0, max_ctx - len(block) - 50)
            context = (context[:room] + '…') if len(context) > room else context
        # Dá prioridade ao anexo: coloca-o no início do contexto.
        context = (block + '\n\n' + (context or '').strip())[:max_ctx]
        fname = (attachment_filename or 'anexo.pdf')[:200]
        excerpt = att[:400] + ('…' if len(att) > 400 else '')
        sources.append(
            {
                'document_id': 0,
                'chunk_index': 0,
                'original_name': fname,
                'excerpt': excerpt,
            }
        )

    answer = generate_rag_answer(context, question)
    return {'answer': answer, 'sources': sources}


_GEN_KIND_LABELS: dict[str, str] = {
    'summary': 'Resumo',
    'exercise_list': 'Lista de exercícios',
    'roadmap': 'Roadmap',
}


def _build_generate_prompt(
    kind: str, *, title: str, topic: str, instructions: str
) -> tuple[str, str]:
    """
    Devolve (system_prompt, question) para o pipeline RAG.
    O output deve ser Markdown bem estruturado e pronto para renderização.
    """
    kind_label = _GEN_KIND_LABELS.get(kind, kind)
    t = (title or '').strip()
    tp = (topic or '').strip()
    extra = (instructions or '').strip()

    header = f'Tipo: {kind_label}'
    if t:
        header += f'\nTítulo: {t}'
    if tp:
        header += f'\nTema: {tp}'
    if extra:
        header += f'\nInstruções adicionais: {extra}'

    system = (
        'Tu és um assistente de estudos. Responde APENAS com base no contexto fornecido (trechos dos PDFs). '
        'Se o contexto não for suficiente, escreve uma secção "Lacunas no material" com o que falta e perguntas '
        'objetivas para o utilizador.\n\n'
        'Formato obrigatório: devolve somente Markdown. Usa títulos, listas, tabelas simples e blocos quando fizer sentido. '
        'Não inventes referências, autores, datas ou definições que não estejam no contexto.'
    )

    if kind == 'summary':
        question = (
            f'{header}\n\n'
            'Gera um resumo de estudo bonito e organizado, com:\n'
            '- visão geral em 5–8 bullets\n'
            '- conceitos-chave (definições curtas)\n'
            '- relações/fluxo (se houver)\n'
            '- exemplos (se existirem nos trechos)\n'
            '- "Checklist de revisão" (5–10 itens)\n'
        )
    elif kind == 'exercise_list':
        question = (
            f'{header}\n\n'
            'Gera uma lista de exercícios progressiva baseada no material, com:\n'
            '- aquecimento (3–5 questões)\n'
            '- nível intermédio (5–8)\n'
            '- avançado/desafio (2–4)\n'
            '- uma secção "gabarito/guia" com pistas curtas (não soluções completas) quando possível\n'
            'Os exercícios devem referir-se explicitamente a conceitos presentes no contexto.'
        )
    elif kind == 'roadmap':
        question = (
            f'{header}\n\n'
            'Gera um roadmap de estudo inteligente e prático baseado no material, com:\n'
            '- pré-requisitos\n'
            '- trilha em etapas (do básico ao avançado), com objetivos e critérios de domínio\n'
            '- tarefas/atividades sugeridas por etapa\n'
            '- pontos de verificação (autoavaliação)\n'
            'Não incluas recursos externos; usa só o que estiver no contexto.'
        )
    else:
        question = f'{header}\n\nGera um documento de estudo bem estruturado e útil.'

    return system, question


def run_rag_generate_for_user(
    *,
    user_id: int,
    kind: str,
    title: str = '',
    topic: str = '',
    instructions: str = '',
    document_ids: list[int] | None,
) -> dict[str, Any]:
    """
    Geração de materiais: retrieval via Chroma + LLM, devolvendo Markdown e sources.
    """
    from .chroma_index import search_similar_chunks

    sys_prompt, question = _build_generate_prompt(
        kind,
        title=title,
        topic=topic,
        instructions=instructions,
    )

    top_k = max(int(getattr(settings, 'RAG_TOP_K', 5)), 5)
    gen_top_k = int(getattr(settings, 'RAG_GENERATE_TOP_K', top_k * 3))
    # Se o utilizador forneceu um tema, dá-lhe peso como "query"
    embed_text = (topic or '').strip() or question
    embedding = embed_question(embed_text)

    chunks = search_similar_chunks(
        embedding,
        user_id=user_id,
        top_k=gen_top_k,
        document_ids=document_ids,
    )
    context, sources = build_context_from_chunks(
        chunks,
        max_chars=int(getattr(settings, 'RAG_MAX_CONTEXT_CHARS', 12000)) * 2,
    )
    markdown = generate_rag_answer(context, question, system_prompt=sys_prompt)
    return {
        'kind': kind,
        'title': (title or '').strip() or _GEN_KIND_LABELS.get(kind, kind),
        'markdown': markdown,
        'sources': sources,
    }
