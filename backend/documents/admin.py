from django.contrib import admin
from .models import Document


# Administração do modelo Documento
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):

    list_display = (
        'original_name',
        'user',
        'text_preview',
        'chunk_count',
        'extraction_error',
        'created_at',
    )

    # Filtrar os documentos por data de criação 
    list_filter = ('created_at',)
    # Pesquisar os documentos por nome original ou nome de usuário
    search_fields = ('original_name', 'user__username')
    # Campos somente leitura
    readonly_fields = (
        'created_at',
        'updated_at',
        'extracted_text',
        'extraction_error',
        'chunk_count',
    )

    @admin.display(description='Texto (prévia)')

    # Previsão de texto
    def text_preview(self, obj: Document) -> str:

        t = (obj.extracted_text or '')[:80] # Texto da previsão
        return f'{t}…' if len(obj.extracted_text or '') > 80 else t or '—' # Devolver a previsão
