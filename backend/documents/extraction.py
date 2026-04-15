from __future__ import annotations
from django.conf import settings
from django.utils import timezone
from .chunking import split_into_chunks
from .models import Document
from .ollama_embed import OllamaEmbedError, embed_texts
from .pdf_text import extract_pdf_text


def extract_and_save_document(document: Document) -> None:
    
    # Limpar os embeddings
    def clear_embed() -> None:
        document.embedded_chunk_count = 0
        document.embedding_error = '' # Limpar o erro de embedding

    if not document.file:
        document.extraction_error = 'Sem documento disponível.'
        document.chunk_count = 0
        clear_embed()
        document.save(
            update_fields=[
                'extraction_error',
                'chunk_count',
                'embedded_chunk_count',
                'embedding_error',
                'updated_at',
            ]
        )
        return

    try:

        text = extract_pdf_text(document.file.path)
        document.extracted_text = text
        document.extraction_error = ''

    except ImportError as exc:

        document.extracted_text = ''
        document.chunk_count = 0
        clear_embed()
        document.extraction_error = (
            'Dependência em falta: pip install pypdf'
            if 'pypdf' in str(exc).lower()
            else str(exc)[:500]
        )

    except Exception as exc:
        document.extracted_text = ''
        document.chunk_count = 0
        clear_embed()
        document.extraction_error = str(exc)[:500]

    if not document.extraction_error and document.extracted_text:
        chunks = split_into_chunks(
            document.extracted_text,
            chunk_size=getattr(settings, 'RAG_CHUNK_SIZE', 1500),
            overlap=getattr(settings, 'RAG_CHUNK_OVERLAP', 200),
        )
        
        document.chunk_count = len(chunks)
        if chunks:
            try:
                embed_texts(
                    chunks,
                    base_url=getattr(settings, 'OLLAMA_BASE_URL', 'http://127.0.0.1:11434'),
                    model=getattr(settings, 'OLLAMA_EMBED_MODEL', 'nomic-embed-text:latest'),
                    timeout=float(getattr(settings, 'OLLAMA_EMBED_TIMEOUT', 120)),
                    batch_size=int(getattr(settings, 'OLLAMA_EMBED_BATCH_SIZE', 32)),
                )
                document.embedded_chunk_count = len(chunks)
                document.embedding_error = ''
            except OllamaEmbedError as exc:
                document.embedded_chunk_count = 0
                document.embedding_error = str(exc)[:500]
            except Exception as exc:
                document.embedded_chunk_count = 0
                document.embedding_error = str(exc)[:500]
        else:
            clear_embed()
    elif document.extraction_error:
        document.chunk_count = 0
        clear_embed()

    document.updated_at = timezone.now()
    document.save(
        update_fields=[
            'extracted_text',
            'extraction_error',
            'chunk_count',
            'embedded_chunk_count',
            'embedding_error',
            'updated_at',
        ]
    )
