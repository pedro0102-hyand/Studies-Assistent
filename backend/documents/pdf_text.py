"""Extração de texto de PDFs (pypdf) — import lazy para o Django arrancar sem o pacote instalado."""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_pdf_text(file_path: Path | str) -> str:
    from pypdf import PdfReader

    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f'Ficheiro não encontrado: {path}')

    reader = PdfReader(str(path))
    parts: list[str] = []
    for i, page in enumerate(reader.pages):
        try:
            t = page.extract_text()
            if t:
                parts.append(t)
        except Exception as exc:
            logger.warning('Falha na página %s de %s: %s', i, path, exc)

    return '\n\n'.join(parts).strip()
