from django.conf import settings # Configuração do Django
from django.db import models # Modelo de dados
from django.utils.text import get_valid_filename # Função para validar o nome do ficheiro


# Guarda PDFs por utilizador
def upload_to_user_pdf(instance: 'Document', filename: str) -> str:

    safe = get_valid_filename(filename)
    return f'pdfs/user_{instance.user_id}/{safe}'

# Modelo de Documento
class Document(models.Model):

    # Relação com o utilizador
    user = models.ForeignKey(

        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents',
        
    )

    original_name = models.CharField(max_length=255) # Nome original do ficheiro
    file = models.FileField(upload_to=upload_to_user_pdf) # Ficheiro PDF
    created_at = models.DateTimeField(auto_now_add=True) # Data de criação
    updated_at = models.DateTimeField(auto_now=True) # Data de atualização

    class Meta: # Ordenação dos documentos
        ordering = ['-created_at']

    # String de representação do documento
    def __str__(self) -> str:
        return f'{self.original_name} ({self.user_id})'
