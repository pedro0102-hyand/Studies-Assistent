"""
Etapa 4.5 — persistência de embeddings no ChromaDB (vetores + texto + metadados).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from .models import Document

logger = logging.getLogger(__name__)

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection

    import chromadb

    path = getattr(settings, 'CHROMA_PERSIST_PATH', None)
    name = getattr(settings, 'CHROMA_COLLECTION_NAME', 'study_documents')
    if not path:
        raise RuntimeError('CHROMA_PERSIST_PATH não definido.')

    path = str(path)
    _client = chromadb.PersistentClient(path=path)
    _collection = _client.get_or_create_collection(
        name=name,
        metadata={'app': 'studies_assistant'},
    )
    return _collection


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
