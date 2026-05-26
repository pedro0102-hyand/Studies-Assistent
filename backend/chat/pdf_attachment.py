"""Extração e validação de PDF anexado a uma mensagem de chat.

A persistência na biblioteca (modelo ``Document``) é feita na view de mensagens.
"""

from __future__ import annotations

from django.conf import settings

from documents.pdf_text import extract_pdf_text_from_bytes
from documents.pdf_validation import MAX_PDF_BYTES, validate_pdf_bytes, validate_pdf_upload


class ChatAttachmentError(Exception):
    """Ficheiro inválido ou extração falhou."""


def extract_text_from_uploaded_pdf(uploaded) -> str:
    """
    `uploaded`: UploadedFile do Django.
    Devolve texto extraído ou levanta ChatAttachmentError.
    """
    if not uploaded:
        raise ChatAttachmentError('Ficheiro em falta.')

    try:
        validate_pdf_upload(uploaded)
        uploaded.seek(0)
        data = uploaded.read()
        validate_pdf_bytes(data)
    except ValueError as exc:
        raise ChatAttachmentError(str(exc)) from exc

    try:
        return extract_pdf_text_from_bytes(data)
    except ImportError as exc:
        raise ChatAttachmentError(
            'Dependência em falta: pip install pypdf'
        ) from exc
    except Exception as exc:
        raise ChatAttachmentError(f'Não foi possível ler o PDF: {exc}') from exc


def truncate_for_rag(text: str) -> str:
    max_chars = max(
        500,
        int(getattr(settings, 'RAG_MAX_CHAT_ATTACHMENT_CONTEXT_CHARS', 8000)),
    )
    t = (text or '').strip()
    if len(t) <= max_chars:
        return t
    return t[: max_chars - 1] + '…'
