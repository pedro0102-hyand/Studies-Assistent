"""
Divisão do texto em chunks com overlap.

- Normalização de espaços em branco típicos de PDFs.
- Fim de chunk preferencial em separadores naturais (parágrafo, linha, frase, espaço).
- Após cada chunk, o próximo começa em `end - overlap`, alinhado **para trás** ao início
  da palavra se o índice cair a meio — preserva continuidade (não se salta texto para a frente).
- Fragmentos muito curtos (< 400 chars) são fundidos ao chunk anterior quando este já
  é grande (~650+ chars), para evitar blocos desligados (ex.: só cabeçalho de página).
"""
from __future__ import annotations

import re

# Separadores do mais forte ao mais fraco (ordem de preferência para «snap» do fim do chunk)
_SNAP_SEPARATORS = ('\n\n', '\n', '. ', '? ', '! ', '; ', ', ', ' ')


def normalize_extracted_text(text: str) -> str:
    """
    Reduz ruído comum em texto vindo de PDF: blocos de linhas vazias, espaços repetidos.
    """
    if not text:
        return ''
    t = text.replace('\r\n', '\n').replace('\r', '\n')
    t = re.sub(r'\n{3,}', '\n\n', t)
    t = re.sub(r'[ \t]+\n', '\n', t)
    t = re.sub(r'[ \t]{2,}', ' ', t)
    return t.strip()


def _align_overlap_start_backward(text: str, next_start: int, max_back: int = 160) -> int:
    """
    Quando `end - overlap` cai no meio de uma palavra, **recua** até ao início
    dessa palavra (no máximo `max_back` caracteres).

    Isto preserva continuidade entre chunks: não se salta texto para a frente
    (o problema do avanço até ao próximo espaço, que criava «buracos» e chunks
    minúsculos desligados do anterior).
    """
    if next_start <= 0:
        return next_start
    low = max(0, next_start - max_back)
    s = next_start
    while s > low and s < len(text):
        prev, cur = text[s - 1], text[s]
        if prev.isalnum() and cur.isalnum():
            s -= 1
        else:
            break
    return s


def _snap_chunk_end(text: str, start: int, tentative_end: int, min_chunk: int) -> int:
    """
    Ajusta o fim do chunk para o último separador «natural» antes de tentative_end.
    Se o limite cair a meio de palavra (ex.: «viola» | «ções»), recua até ao último espaço
    na janela — mesmo quando min_chunk impedia usar esse espaço antes (era o bug).
    """
    n = len(text)
    tentative_end = min(max(tentative_end, start), n)
    if tentative_end <= start:
        return tentative_end

    window = text[start:tentative_end]
    min_from_start = max(0, min_chunk - 20)

    end = tentative_end
    for sep in _SNAP_SEPARATORS:
        pos = window.rfind(sep)
        if pos >= min_from_start:
            cut = start + pos + len(sep)
            if cut > start:
                end = cut
                break

    # Não deixar o limite exclusivo `end` entre dois caracteres da mesma palavra
    if end < n and text[end - 1].isalnum() and text[end].isalnum():
        sp = text.rfind(' ', start, end)
        if sp > start:
            end = sp + 1

    return end


def _merge_undersized_chunks(
    chunks: list[str],
    *,
    min_len: int = 400,
    max_combined: int = 2800,
    prev_chunk_min: int = 650,
) -> list[str]:
    """
    Junta ao chunk **anterior** apenas pedaços muito curtos (ex.: cabeçalho de página),
    e só se o anterior já for grande o suficiente — evita fundir vários chunks
    legítimos pequenos de testes ou texto sem espaços.
    """
    if len(chunks) <= 1:
        return chunks
    out = [chunks[0]]
    for c in chunks[1:]:
        c = c.strip()
        if not c:
            continue
        prev = out[-1]
        if (
            len(c) < min_len
            and len(prev) >= prev_chunk_min
            and len(prev) + len(c) + 2 <= max_combined
        ):
            out[-1] = prev.rstrip() + '\n\n' + c
        else:
            out.append(c)
    return out


def split_into_chunks(
    text: str,
    *,
    chunk_size: int = 1500,
    overlap: int = 200,
) -> list[str]:
    """
    Janela deslizante com overlap; o fim de cada janela é alinhado a separadores
    quando possível (reduz cortes como «artific» + «lica» no meio de palavras).
    """
    text = normalize_extracted_text(text or '')
    if not text:
        return []

    if chunk_size < 100:
        chunk_size = 100
    if overlap < 0:
        overlap = 0
    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 5)

    min_chunk = min(120, chunk_size // 3)
    chunks: list[str] = []
    start = 0
    n = len(text)

    while start < n:
        tentative_end = min(start + chunk_size, n)
        end = _snap_chunk_end(text, start, tentative_end, min_chunk)

        # Evitar estagnação se o snap devolver o mesmo índice ou chunk vazio
        if end <= start:
            end = min(start + chunk_size, n)
        if end <= start:
            break

        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)

        if end >= n:
            break

        next_start = end - overlap
        if next_start <= start:
            next_start = end
        next_start = _align_overlap_start_backward(text, next_start)
        if next_start <= start:
            next_start = end
        start = next_start

    return _merge_undersized_chunks(chunks)


def chunks_with_indices(text: str, document_id: int, **kwargs) -> list[dict]:
    """Lista de dicts com metadados por chunk (para indexação / Chroma)."""
    parts = split_into_chunks(text, **kwargs)
    return [
        {
            'chunk_index': i,
            'document_id': document_id,
            'text': t,
        }
        for i, t in enumerate(parts)
    ]
