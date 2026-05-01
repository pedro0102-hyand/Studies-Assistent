"""Extração e validação de PDF anexado a uma mensagem de chat (sem gravar Document)."""

from __future__ import annotations

import logging
from io import BytesIO

from django.conf import settings

from documents.serializers import MAX_PDF_BYTES, PDF_MAGIC

logger = logging.getLogger(__name__)


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

    if getattr(uploaded, 'size', 0) > MAX_PDF_BYTES:
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
        from pypdf import PdfReader
    except ImportError as exc:
        raise ChatAttachmentError(
            'Dependência em falta: pip install pypdf'
        ) from exc

    try:
        reader = PdfReader(BytesIO(data))
        parts: list[str] = []
        for i, page in enumerate(reader.pages):
            try:
                t = page.extract_text()
                if t:
                    parts.append(t)
            except Exception as exc:
                logger.warning('Chat PDF: falha na página %s: %s', i, exc)
        return '\n\n'.join(parts).strip()
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
