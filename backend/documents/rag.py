"""
Etapa 5+ — RAG: embedding da pergunta e (mais tarde) retrieval + LLM.
"""
from __future__ import annotations

from typing import Any

from django.conf import settings

from . import ollama_embed
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
