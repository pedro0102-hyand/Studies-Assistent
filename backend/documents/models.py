from django.conf import settings 
from django.db import models 
from django.utils.text import get_valid_filename 


# Guarda PDFs por usuario
def upload_to_user_pdf(instance: 'Document', filename: str) -> str:

    safe = get_valid_filename(filename) 
    return f'pdfs/user_{instance.user_id}/{safe}'

# Modelo de Documento
class Document(models.Model):

  
    user = models.ForeignKey(

        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents',
        
    )

    original_name = models.CharField(max_length=255) # Nome original do ficheiro
    file = models.FileField(upload_to=upload_to_user_pdf) # Ficheiro PDF
    # Etapa 4.2 — texto extraído (pode ser grande; em produção considerar ficheiro à parte)
    extracted_text = models.TextField(blank=True, default='')
    extraction_error = models.CharField(max_length=500, blank=True, default='')
    # Etapa 4.3 — número de chunks gerados a partir de extracted_text
    chunk_count = models.PositiveIntegerField(default=0)
    # Etapa 4.4 — embeddings Ollama (vetores em memória; Chroma na 4.5)
    embedded_chunk_count = models.PositiveIntegerField(default=0)
    embedding_error = models.CharField(max_length=500, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True) # Data de criação
    updated_at = models.DateTimeField(auto_now=True) # Data de atualização

    class Meta: # Ordenação dos documentos
        ordering = ['-created_at']

    # String de representação do documento
    def __str__(self) -> str:
        return f'{self.original_name} ({self.user_id})'
