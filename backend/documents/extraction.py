from __future__ import annotations

from django.utils import timezone

from .models import Document
from .pdf_text import extract_pdf_text


def extract_and_save_document(document: Document) -> None:
    """Grava texto extraído em `document` ou mensagem em `extraction_error`."""
    if not document.file:
        document.extraction_error = 'Sem ficheiro associado.'
        document.save(update_fields=['extraction_error', 'updated_at'])
        return

    try:
        text = extract_pdf_text(document.file.path)
        document.extracted_text = text
        document.extraction_error = ''
    except ImportError as exc:
        document.extracted_text = ''
        document.extraction_error = (
            'Dependência em falta: pip install pypdf'
            if 'pypdf' in str(exc).lower()
            else str(exc)[:500]
        )
    except Exception as exc:
        document.extracted_text = ''
        document.extraction_error = str(exc)[:500]

    document.updated_at = timezone.now()
    document.save(update_fields=['extracted_text', 'extraction_error', 'updated_at'])
