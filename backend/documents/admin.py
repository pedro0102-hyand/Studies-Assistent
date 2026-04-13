from django.contrib import admin

from .models import Document


# Administração do modelo Documento
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):

    list_display = ('original_name', 'user', 'created_at') 
    list_filter = ('created_at',)
    search_fields = ('original_name', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
