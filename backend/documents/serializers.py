import os
from django.conf import settings
from django.utils.text import get_valid_filename
from rest_framework import serializers
from .models import Document

PDF_MAGIC = b'%PDF' # Magic number for PDF files
MAX_PDF_BYTES = 25 * 1024 * 1024  # 25 MB  Maximum size for PDF files

# Serializer for Document detail
class DocumentDetailSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    text_char_count = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            'id',
            'original_name',
            'file_url',
            'text_char_count',
            'chunk_count',
            'embedded_chunk_count',
            'embedding_error',
            'chroma_indexed_at',
            'chroma_error',
            'extraction_error',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields

    def get_text_char_count(self, obj: Document) -> int:
        return len(obj.extracted_text or '')

    # Get the URL of the file
    def get_file_url(self, obj: Document) -> str:

        request = self.context.get('request') # Get the request

        if not obj.file:
            return ''
        url = obj.file.url # Get the URL of the file
        if request:
            return request.build_absolute_uri(url) # Build the absolute URI
        return url

# Serializer for Document upload
class DocumentUploadSerializer(serializers.Serializer):

    file = serializers.FileField(write_only=True) # File field for the PDF file

    def validate_file(self, value): # Validate the file

        if value.size > MAX_PDF_BYTES: # Check if the file size is greater than the maximum size
            raise serializers.ValidationError(
                f'O ficheiro excede o limite de {MAX_PDF_BYTES // (1024 * 1024)} MB.'
            )

        name = (value.name or '').lower()
        if not name.endswith('.pdf'):
            raise serializers.ValidationError('Apenas ficheiros .pdf são permitidos.')

        value.open('rb')
        try:
            head = value.read(4)
        finally:
            value.seek(0)

        if head != PDF_MAGIC:
            raise serializers.ValidationError(
                'O conteúdo não é um PDF válido (cabeçalho %PDF).'
            )

        return value

    def create(self, validated_data): # Create the document

        request = self.context['request'] # Get the request
        f = validated_data['file']
        original_name = get_valid_filename(os.path.basename(f.name or 'document.pdf')) # Get the original name of the file

        return Document.objects.create(
            # Create the document
            user=request.user,
            original_name=original_name,
            file=f,

        )


# --- Etapa 5.1 — contrato JSON do endpoint RAG (perguntar aos PDFs) ---


class RagAskRequestSerializer(serializers.Serializer):
    """
    POST /api/rag/ask/ — corpo do pedido.

    - question: texto da pergunta (obrigatório).
    - document_ids: opcional; se presente, restringe a recuperação a estes IDs de Document
      do utilizador (validação de posse no serviço RAG).
    """

    question = serializers.CharField(
        trim_whitespace=True,
        min_length=1,
        max_length=getattr(settings, 'RAG_MAX_QUESTION_LENGTH', 4000),
    )
    document_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_null=True,
        max_length=getattr(settings, 'RAG_MAX_FILTER_DOCUMENTS', 20),
    )

    def validate_document_ids(self, value):
        if value is None:
            return None
        if len(value) == 0:
            return None
        # IDs únicos, ordem estável
        seen: set[int] = set()
        out: list[int] = []
        for x in value:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out


class RagSourceSerializer(serializers.Serializer):
    """Uma fonte citada na resposta (chunk recuperado)."""

    document_id = serializers.IntegerField()
    chunk_index = serializers.IntegerField(min_value=0)
    original_name = serializers.CharField()
    excerpt = serializers.CharField()


class RagAskResponseSerializer(serializers.Serializer):
    """
    Corpo da resposta de sucesso do RAG.

    - answer: texto gerado pelo modelo.
    - sources: trechos usados como contexto (opcional mas recomendado para transparência).
    """

    answer = serializers.CharField()
    sources = RagSourceSerializer(many=True, required=False)
