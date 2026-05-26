"""Validação partilhada para PDFs (upload e anexos no chat).

Centraliza regras para evitar divergências:
- limite de tamanho (25 MB)
- extensão .pdf
- cabeçalho %PDF

Este módulo é deliberadamente agnóstico a DRF/Django (levanta ValueError).
"""

from __future__ import annotations

PDF_MAGIC = b"%PDF"
MAX_PDF_BYTES = 25 * 1024 * 1024  # 25 MB


def validate_pdf_upload(uploaded) -> None:
    """
    Valida um UploadedFile do Django.

    Levanta ValueError com mensagem em PT quando inválido.
    Não consome o stream (restaura o cursor para o início).
    """
    if not uploaded:
        raise ValueError("Ficheiro em falta.")

    name = (getattr(uploaded, "name", "") or "").lower()
    if not name.endswith(".pdf"):
        raise ValueError("Apenas ficheiros .pdf são permitidos.")

    size = getattr(uploaded, "size", 0) or 0
    if size and size > MAX_PDF_BYTES:
        raise ValueError(
            f"O PDF excede o limite de {MAX_PDF_BYTES // (1024 * 1024)} MB."
        )

    # Lê só o cabeçalho e volta ao início.
    try:
        uploaded.seek(0)
        head = uploaded.read(4)
    finally:
        try:
            uploaded.seek(0)
        except Exception:
            pass

    if head != PDF_MAGIC:
        raise ValueError("O ficheiro não é um PDF válido (cabeçalho %PDF).")


def validate_pdf_bytes(data: bytes) -> None:
    """Valida bytes já carregados na memória."""
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError("Conteúdo inválido.")
    if len(data) > MAX_PDF_BYTES:
        raise ValueError(
            f"O PDF excede o limite de {MAX_PDF_BYTES // (1024 * 1024)} MB."
        )
    if data[:4] != PDF_MAGIC:
        raise ValueError("O ficheiro não é um PDF válido (cabeçalho %PDF).")

