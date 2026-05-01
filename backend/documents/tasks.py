from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def process_document_extraction(document_id: int) -> None:
    """Extrai texto, embeddings e Chroma num worker Celery (ou síncrono se eager)."""
    from .extraction import extract_and_save_document
    from .models import Document

    try:
        doc = Document.objects.get(pk=document_id)
    except Document.DoesNotExist:
        logger.warning('Celery: documento %s não existe.', document_id)
        return

    try:
        Document.objects.filter(pk=document_id).update(extraction_status='processing')
        extract_and_save_document(Document.objects.get(pk=document_id))
    except Exception as exc:
        logger.exception('Celery: falha ao processar documento %s', document_id)
        Document.objects.filter(pk=document_id).update(
            extraction_status='failed',
            extraction_error=str(exc)[:500],
        )
        return

    doc = Document.objects.get(pk=document_id)
    final = 'failed' if doc.extraction_error else 'done'
    Document.objects.filter(pk=document_id).update(extraction_status=final)
