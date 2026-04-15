from __future__ import annotations

# Dividir o texto em chunks com overlap (por caracteres)
def split_into_chunks(
    text: str,
    *,
    chunk_size: int = 1500,
    overlap: int = 200,
) -> list[str]:
    
    text = (text or '').strip() # Remover espaços em branco

    # Se o texto estiver vazio, retornar uma lista vazia
    if not text:
        return []

    if chunk_size < 100:
        chunk_size = 100

    if overlap < 0:
        overlap = 0

    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 5)

    step = chunk_size - overlap 
    chunks: list[str] = [] # Lista para armazenar os chunks
    start = 0 # Início do texto
    n = len(text) # Comprimento do texto

    while start < n:

        end = min(start + chunk_size, n) # Fim do texto
        piece = text[start:end].strip() # Texto do chunk

        if piece:
            chunks.append(piece) # Adicionar o chunk à lista
        if end >= n:
            break
        start += step

    return chunks

# Lista de dicts com metadados por chunk (para indexação / Chroma)
def chunks_with_indices(text: str, document_id: int, **kwargs) -> list[dict]:
    
    parts = split_into_chunks(text, **kwargs) # Dividir o texto em chunks

    # Devolver a lista de chunks com os metadados
    return [
        {
            'chunk_index': i,
            'document_id': document_id,
            'text': t,
        }
        for i, t in enumerate(parts)
    ]
