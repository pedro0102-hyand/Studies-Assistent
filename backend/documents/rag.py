"""
Etapa 5+ — RAG: embedding da pergunta e (mais tarde) retrieval + LLM.
"""
from __future__ import annotations

from django.conf import settings

from . import ollama_embed
from .ollama_embed import OllamaEmbedError


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
