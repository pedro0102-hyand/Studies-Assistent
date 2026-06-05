"""Utilitários partilhados entre views e serializers de documentos."""

from __future__ import annotations

import threading

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser

from .models import Document
from .ollama_chat import OllamaChatError
from .ollama_embed import OllamaEmbedError
from .tasks import process_document_extraction

INVALID_DOCUMENT_IDS_DETAIL = (
    'Um ou mais document_ids são inválidos ou não pertencem ao utilizador.'
)
DOCUMENT_LIMIT_REACHED_DETAIL = (
    'Atingiste o número máximo de documentos para esta conta.'
)


def document_limit_reached_for_user(user: AbstractBaseUser) -> bool:
    """True se o utilizador atingiu DOCUMENT_MAX_PER_USER."""
    limit = int(getattr(settings, 'DOCUMENT_MAX_PER_USER', 500))
    return limit > 0 and Document.objects.filter(user=user).count() >= limit


def normalize_document_ids(value: list[int] | None) -> list[int] | None:
    """Remove duplicados mantendo a ordem; None se vazio ou ausente."""
    if value is None or len(value) == 0:
        return None
    seen: set[int] = set()
    out: list[int] = []
    for doc_id in value:
        if doc_id not in seen:
            seen.add(doc_id)
            out.append(doc_id)
    return out


def document_ids_invalid_for_user(
    user: AbstractBaseUser,
    document_ids: list[int] | None,
) -> bool:
    """True se algum ID não existir ou não pertencer ao utilizador."""
    if document_ids is None:
        return False
    found = set(
        Document.objects.filter(user=user, pk__in=document_ids).values_list(
            'pk', flat=True
        )
    )
    return set(document_ids) != found


def enqueue_document_extraction(document_id: int) -> str | None:
    """
    Enfileira extração via Celery; em DEBUG sem broker, executa numa thread.

    Devolve mensagem de erro em produção se a fila falhar; None se OK.
    """
    try:
        process_document_extraction.delay(document_id)
        return None
    except Exception:
        if getattr(settings, 'DEBUG', False):
            threading.Thread(
                target=process_document_extraction,
                args=(document_id,),
                daemon=True,
            ).start()
            return None
        return 'Fila de processamento indisponível (Celery/Redis).'


def run_rag_or_error(run_fn):
    """Executa pipeline RAG e mapeia exceções conhecidas para respostas HTTP."""
    try:
        return run_fn(), None
    except ValueError as exc:
        return None, (str(exc), 400)
    except OllamaEmbedError as exc:
        return None, (str(exc), 502)
    except OllamaChatError as exc:
        return None, (str(exc), 502)
    except RuntimeError as exc:
        return None, (str(exc), 503)
