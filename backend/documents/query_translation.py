"""
Query translation para RAG multilíngue.

Problema: documentos em inglês + pergunta em português → embeddings em "espaços"
semânticos diferentes → similaridade baixa → RAG não encontra nada.

Solução: antes de embedar a pergunta, detectar o idioma e, se não for inglês,
gerar uma versão em inglês via LLM. O embedding é feito sobre a versão inglesa,
mas a resposta final continua sendo gerada na língua original da pergunta.

Estratégia: "query expansion multilíngue"
  - Chamada leve ao LLM (max_tokens pequeno, sem contexto de documentos)
  - Se falhar por qualquer motivo, usa a pergunta original (sem quebrar o fluxo)
  - Configurável via settings: RAG_QUERY_TRANSLATION_ENABLED (default: True)
"""
from __future__ import annotations

import logging

from django.conf import settings

logger = logging.getLogger(__name__)

# Prompt minimalista — queremos apenas a tradução, sem explicações
_SYSTEM_TRANSLATE = (
    "You are a translation assistant. "
    "Translate the user's question to English. "
    "Output ONLY the translated question, nothing else. "
    "If the question is already in English, output it unchanged."
)


def _is_likely_english(text: str) -> bool:
    """
    Heurística rápida: se > 70% dos caracteres forem ASCII e não houver
    caracteres típicos do português (ã, ç, õ, á, é, í, ó, ú, â, ê, ô, à),
    consideramos inglês e pulamos a tradução.
    """
    pt_chars = set("ãçõáéíóúâêôàÃÇÕÁÉÍÓÚÂÊÔÀ")
    if any(c in pt_chars for c in text):
        return False
    ascii_count = sum(1 for c in text if ord(c) < 128)
    return (ascii_count / max(len(text), 1)) > 0.90


def translate_query_to_english(
    question: str,
    *,
    base_url: str,
    model: str,
    timeout: float = 30.0,
) -> str:
    """
    Traduz a pergunta para inglês usando o LLM do Ollama.
    
    Retorna a pergunta traduzida, ou a original em caso de erro.
    Nunca lança exceção — o pipeline RAG não deve ser interrompido por isso.
    """
    q = (question or "").strip()
    if not q:
        return q

    # Otimização: se já parece inglês, não faz a chamada
    if _is_likely_english(q):
        logger.debug("query_translation: pergunta parece ser inglês, pulando tradução.")
        return q

    try:
        from .ollama_chat import ollama_chat_completion  # import relativo dentro do app
    except ImportError:
        # Quando chamado fora do contexto do app (ex.: testes isolados)
        try:
            from documents.ollama_chat import ollama_chat_completion
        except ImportError:
            logger.warning("query_translation: não foi possível importar ollama_chat.")
            return q

    try:
        translated = ollama_chat_completion(
            [
                {"role": "system", "content": _SYSTEM_TRANSLATE},
                {"role": "user", "content": q},
            ],
            base_url=base_url,
            model=model,
            timeout=timeout,
        )
        translated = (translated or "").strip()
        if translated:
            logger.debug(
                "query_translation: '%s' → '%s'",
                q[:60],
                translated[:60],
            )
            return translated
        return q
    except Exception as exc:
        logger.warning("query_translation: falha na tradução (%s), usando original.", exc)
        return q


def maybe_translate_query(question: str) -> str:
    """
    Ponto de entrada principal para o pipeline RAG.
    
    Lê as configurações do Django e decide se traduz ou não.
    Configurações relevantes (todas opcionais, com defaults seguros):
      - RAG_QUERY_TRANSLATION_ENABLED: bool, default True
      - RAG_QUERY_TRANSLATION_MODEL: str, default = OLLAMA_CHAT_MODEL
      - RAG_QUERY_TRANSLATION_TIMEOUT: float, default 30.0
    """
    enabled = getattr(settings, "RAG_QUERY_TRANSLATION_ENABLED", True)
    if not enabled:
        return question

    base_url = getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    # Por defeito usa o mesmo modelo de chat; pode ser overridden para um modelo
    # mais leve (ex.: gemma2:2b é suficiente para tradução simples)
    model = getattr(
        settings,
        "RAG_QUERY_TRANSLATION_MODEL",
        getattr(settings, "OLLAMA_CHAT_MODEL", "gemma2:2b"),
    )
    timeout = float(getattr(settings, "RAG_QUERY_TRANSLATION_TIMEOUT", 30.0))

    return translate_query_to_english(
        question,
        base_url=base_url,
        model=model,
        timeout=timeout,
    )