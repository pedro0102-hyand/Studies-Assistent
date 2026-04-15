from __future__ import annotations
from django.conf import settings
from django.utils import timezone
from .chunking import split_into_chunks
from .models import Document
from .pdf_text import extract_pdf_text

# Extrair e salvar o documento
def extract_and_save_document(document: Document) -> None:
    
    if not document.file:

        document.extraction_error = 'Sem documento .'
        document.chunk_count = 0 # Contagem de chunks
        document.save(update_fields=['extraction_error', 'chunk_count', 'updated_at'])

        return

    try:

        text = extract_pdf_text(document.file.path)
        document.extracted_text = text
        document.extraction_error = ''

    except ImportError as exc:

        document.extracted_text = ''
        document.chunk_count = 0

        document.extraction_error = (

            'Dependência em falta: pip install pypdf'
            if 'pypdf' in str(exc).lower()
            else 
            str(exc)[:500]
        )


    except Exception as exc:

        document.extracted_text = ''
        document.chunk_count = 0
        document.extraction_error = str(exc)[:500]

    if not document.extraction_error and document.extracted_text:

        # Dividir o texto em chunks
        chunks = split_into_chunks(

            document.extracted_text,
            chunk_size=getattr(settings, 'RAG_CHUNK_SIZE', 1500), # Tamanho do chunk
            overlap=getattr(settings, 'RAG_CHUNK_OVERLAP', 200), # Overlap do chunk

        )

        document.chunk_count = len(chunks) # Contagem de chunks

    elif document.extraction_error:
        document.chunk_count = 0

    document.updated_at = timezone.now() # Data de atualização

    # Salvar o documento
    document.save(
        update_fields=[
            'extracted_text',
            'extraction_error',
            'chunk_count',
            'updated_at',
        ]

    )
