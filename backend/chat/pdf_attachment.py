"""Extração e validação de PDF anexado a uma mensagem de chat.

A persistência na biblioteca (modelo ``Document``) é feita na view de mensagens.
"""

from __future__ import annotations

from django.conf import settings

from documents.pdf_text import extract_pdf_text_from_bytes
from documents.serializers import MAX_PDF_BYTES, PDF_MAGIC


class ChatAttachmentError(Exception):
    """Ficheiro inválido ou extração falhou."""


def extract_text_from_uploaded_pdf(uploaded) -> str:
    """
    `uploaded`: UploadedFile do Django.
    Devolve texto extraído ou levanta ChatAttachmentError.
    """
    if not uploaded:
        raise ChatAttachmentError('Ficheiro em falta.')

    name = (getattr(uploaded, 'name', '') or '').lower()
    if not name.endswith('.pdf'):
        raise ChatAttachmentError('Apenas ficheiros .pdf são permitidos no chat.')

    size = getattr(uploaded, 'size', 0)
    if size > MAX_PDF_BYTES:
        raise ChatAttachmentError(
            f'O PDF excede o limite de {MAX_PDF_BYTES // (1024 * 1024)} MB.'
        )

    uploaded.seek(0)
    head = uploaded.read(4)
    uploaded.seek(0)
    if head != PDF_MAGIC:
        raise ChatAttachmentError('O ficheiro não é um PDF válido (cabeçalho %PDF).')

    data = uploaded.read()
    if len(data) > MAX_PDF_BYTES:
        raise ChatAttachmentError(
            f'O PDF excede o limite de {MAX_PDF_BYTES // (1024 * 1024)} MB.'
        )

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
