from __future__ import annotations

import math
from typing import Any

import httpx


class OllamaEmbedError(Exception):
    """Falha ao obter embeddings (rede, HTTP ou resposta inválida)."""


def vector_summary(vec: list[float]) -> dict[str, float | int]:
    """Estatísticas simples de um vetor de embedding (para debug / CLI)."""
    if not vec:
        return {'dim': 0, 'min': 0.0, 'max': 0.0, 'mean': 0.0, 'l2': 0.0}
    n = len(vec)
    s = sum(vec)
    return {
        'dim': n,
        'min': min(vec),
        'max': max(vec),
        'mean': s / n,
        'l2': math.sqrt(sum(x * x for x in vec)),
    }


# Parsear a resposta do Ollama
def _parse_embed_response(data: dict[str, Any], expected_n: int) -> list[list[float]]:

    embeddings = data.get('embeddings') # Obter os embeddings

    if not isinstance(embeddings, list): # Verificar se os embeddings são uma lista

        raise OllamaEmbedError('Resposta sem lista `embeddings`.') # Erro se os embeddings não forem uma lista

    if len(embeddings) != expected_n: # Verificar se o número de embeddings é o esperado

        raise OllamaEmbedError(
            f'Número de embeddings ({len(embeddings)}) diferente do pedido ({expected_n}).'
        )

    out: list[list[float]] = [] # Lista para armazenar os embeddings

    for i, row in enumerate(embeddings): # Iterar sobre os embeddings

        if not isinstance(row, list) or not row: # Verificar se o embedding é uma lista e não vazia
            raise OllamaEmbedError(f'Embedding inválido no índice {i}.')

        try:

            out.append([float(x) for x in row])
        except (TypeError, ValueError) as exc:
            raise OllamaEmbedError(f'Embedding não numérico no índice {i}.') from exc
    return out

# Gerar embeddings via API HTTP do Ollama
def embed_texts(

    texts: list[str], # Lista de textos
    *,
    base_url: str, # URL base do Ollama
    model: str, # Modelo do Ollama
    timeout: float = 120.0, # Tempo de timeout
    batch_size: int = 32, # Tamanho do lote

) -> list[list[float]]: # Devolver a lista de embeddings
    
    if not texts: # Verificar se a lista de textos não está vazia
        return []
    if batch_size < 1: # Verificar se o tamanho do lote é maior que 0
        batch_size = 32

    url = f'{base_url.rstrip("/")}/api/embed' # URL da API do Ollama
    all_vecs: list[list[float]] = [] # Lista para armazenar os embeddings

    with httpx.Client(timeout=timeout) as client: # Cliente HTTP

        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            try:
                resp = client.post(
                    url,
                    json={
                        'model': model,
                        'input': batch,
                        'truncate': True,
                    },
                )

            except httpx.RequestError as exc:
                raise OllamaEmbedError(
                    f'Não foi possível contactar o Ollama em {base_url}: {exc}'
                ) from exc

            if resp.status_code >= 400:

                detail = resp.text[:400] if resp.text else resp.reason_phrase

                try:
                    err_body = resp.json()

                    if isinstance(err_body, dict) and 'error' in err_body:

                        detail = str(err_body['error'])[:500]
                except Exception:
                    pass
                raise OllamaEmbedError(
                    f'Ollama HTTP {resp.status_code}: {detail}'
                )

            try:
                data = resp.json()
            except ValueError as exc:
                raise OllamaEmbedError('Resposta JSON inválida do Ollama.') from exc

            if not isinstance(data, dict):
                raise OllamaEmbedError('Resposta inesperada do Ollama.')

            all_vecs.extend(_parse_embed_response(data, len(batch))) # Adicionar os embeddings à lista

    return all_vecs # Devolver a lista de embeddings
