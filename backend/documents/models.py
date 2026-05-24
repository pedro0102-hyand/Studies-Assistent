from django.conf import settings
from django.db import models
from django.utils.text import get_valid_filename


def upload_to_user_pdf(instance: 'Document', filename: str) -> str:
    safe = get_valid_filename(filename)
    return f'pdfs/user_{instance.user_id}/{safe}'


class Document(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents',
    )
    original_name = models.CharField(max_length=255)
    file = models.FileField(upload_to=upload_to_user_pdf)
    extracted_text = models.TextField(blank=True, default='')
    extraction_error = models.CharField(max_length=500, blank=True, default='')
    chunk_count = models.PositiveIntegerField(default=0)
    embedded_chunk_count = models.PositiveIntegerField(default=0)
    embedding_error = models.CharField(max_length=500, blank=True, default='')
    chroma_indexed_at = models.DateTimeField(null=True, blank=True)
    chroma_error = models.CharField(max_length=500, blank=True, default='')
    extraction_status = models.CharField(
        max_length=16,
        choices=[
            ('pending', 'Em fila'),
            ('processing', 'A processar'),
            ('done', 'Concluído'),
            ('failed', 'Falhou'),
        ],
        default='pending',
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.original_name} ({self.user_id})'
