"""
Etapa 4.5 — persistência de embeddings no ChromaDB (vetores + texto + metadados).

O cliente Chroma é mantido por processo (lazy + thread-safe). Cada worker do
Gunicorn é um processo separado com a sua própria instância; não há estado
partilhado entre workers — o armazenamento em disco é a fonte de verdade.
"""
from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, Any, NamedTuple

from django.conf import settings

if TYPE_CHECKING:
    from .models import Document

logger = logging.getLogger(__name__)

_chroma_lock = threading.Lock()
_chroma: '_ChromaBundle | None' = None


class _ChromaBundle(NamedTuple):
    client: Any
    collection: Any


def _get_collection():
    global _chroma
    if _chroma is not None:
        return _chroma.collection

    import chromadb

    path = getattr(settings, 'CHROMA_PERSIST_PATH', None)
    name = getattr(settings, 'CHROMA_COLLECTION_NAME', 'study_documents')
    if not path:
        raise RuntimeError('CHROMA_PERSIST_PATH não definido.')

    path = str(path)
    with _chroma_lock:
        if _chroma is not None:
            return _chroma.collection
        client = chromadb.PersistentClient(path=path)
        collection = client.get_or_create_collection(
            name=name,
            metadata={'app': 'studies_assistant'},
        )
        _chroma = _ChromaBundle(client=client, collection=collection)
        return _chroma.collection


def delete_chroma_for_document(document_id: int) -> None:
    """Remove todos os pontos associados a um Document (por metadata `document_id`)."""
    if document_id <= 0:
        return
    try:
        coll = _get_collection()
    except Exception as exc:
        logger.warning('Chroma: não foi possível abrir a coleção para apagar doc %s: %s', document_id, exc)
        return

    try:
        coll.delete(where={'document_id': document_id})
    except Exception:
        try:
            coll.delete(where={'document_id': {'$eq': document_id}})
        except Exception as exc:
            logger.warning('Chroma: falha ao apagar vetores do documento %s: %s', document_id, exc)


def upsert_document_to_chroma(
    document: 'Document',
    chunks: list[str],
    embeddings: list[list[float]],
) -> None:
    """
    Substitui os vetores deste documento na coleção (apaga entradas antigas e adiciona as novas).
    """
    if len(chunks) != len(embeddings):
        raise ValueError('chunks e embeddings devem ter o mesmo comprimento.')

    coll = _get_collection()
    doc_id = document.pk
    delete_chroma_for_document(doc_id)

    if not chunks:
        return

    ids = [f'd{doc_id}_c{i}' for i in range(len(chunks))]
    metadatas = [
        {
            'document_id': doc_id,
            'chunk_index': i,
            'user_id': document.user_id,
            'original_name': (document.original_name or '')[:200],
        }
        for i in range(len(chunks))
    ]

    coll.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )


def _where_rag(user_id: int, document_ids: list[int] | None) -> dict[str, Any]:
    """Filtro obrigatório por user_id; opcionalmente restringe a document_id ∈ document_ids."""
    base: dict[str, Any] = {'user_id': user_id}
    if not document_ids:
        return base
    return {'$and': [base, {'document_id': {'$in': document_ids}}]}


def search_similar_chunks(
    query_embedding: list[float],
    user_id: int,
    top_k: int | None = None,
    document_ids: list[int] | None = None,
) -> list[dict[str, Any]]:
    """
    Etapa 5.3 — pesquisa por similaridade no Chroma com isolamento por utilizador.

    - `user_id` é obrigatório nos metadados (nunca pesquisar sem este filtro).
    - `document_ids`, se preenchido, limita aos documentos indicados (após validação
      de posse na camada RAG).
    Devolve uma lista ordenada por relevância (Chroma), cada item com:
    `document` (texto do chunk), `metadata`, `distance`.
    """
    if user_id < 1:
        raise ValueError('user_id tem de ser um identificador válido para RAG.')
    if not query_embedding:
        raise ValueError('query_embedding não pode ser vazio.')

    k_raw = top_k if top_k is not None else int(
        getattr(settings, 'RAG_TOP_K', 5)
    )
    k = max(1, min(50, k_raw))

    coll = _get_collection()
    where = _where_rag(user_id, document_ids)

    try:
        raw = coll.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where,
            include=['documents', 'metadatas', 'distances'],
        )
    except Exception as exc:
        logger.warning('Chroma query RAG falhou (user_id=%s): %s', user_id, exc)
        raise RuntimeError(
            'Não foi possível consultar o índice de vetores. Verifica CHROMA_PERSIST_PATH e o serviço.'
        ) from exc

    docs_batch = raw.get('documents') or []
    meta_batch = raw.get('metadatas') or []
    dist_batch = raw.get('distances') or []
    if not docs_batch or not docs_batch[0]:
        return []

    documents = docs_batch[0]
    metadatas = meta_batch[0] if meta_batch and meta_batch[0] else [{}] * len(documents)
    distances = dist_batch[0] if dist_batch and dist_batch[0] else [None] * len(documents)

    out: list[dict[str, Any]] = []
    for i, text in enumerate(documents):
        if text is None:
            continue
        meta = metadatas[i] if i < len(metadatas) else {}
        if meta is None:
            meta = {}
        dist = distances[i] if i < len(distances) else None
        out.append(
            {
                'document': text,
                'metadata': dict(meta),
                'distance': dist,
            }
        )
    return out
