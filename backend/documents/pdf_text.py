"""Extração de texto de PDFs (pypdf) — import lazy para o Django arrancar sem o pacote instalado."""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

logger = logging.getLogger(__name__)


def _extract_text_from_reader(reader, *, page_log_suffix: str = '') -> str:
    parts: list[str] = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text()
            if text:
                parts.append(text)
        except Exception as exc:
            logger.warning('Falha na página %s%s: %s', i, page_log_suffix, exc)
    return '\n\n'.join(parts).strip()


def extract_pdf_text_from_bytes(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(data))
    return _extract_text_from_reader(reader)


def extract_pdf_text(file_path: Path | str) -> str:
    from pypdf import PdfReader

    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f'Ficheiro não encontrado: {path}')

    reader = PdfReader(str(path))
    return _extract_text_from_reader(reader, page_log_suffix=f' de {path}')
