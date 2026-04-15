from django.contrib import admin
from .models import Document


# Administração do modelo Documento
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):

    list_display = ('original_name', 'user', 'text_preview', 'extraction_error', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('original_name', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'extracted_text', 'extraction_error')

    @admin.display(description='Texto (prévia)')
    def text_preview(self, obj: Document) -> str:
        t = (obj.extracted_text or '')[:80]
        return f'{t}…' if len(obj.extracted_text or '') > 80 else t or '—'
