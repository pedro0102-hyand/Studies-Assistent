import os

from django.conf import settings
from django.utils.text import get_valid_filename
from rest_framework import serializers

from .models import Document
from .pdf_validation import MAX_PDF_BYTES, validate_pdf_upload
from .utils import normalize_document_ids


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
            'extraction_status',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields

    def get_text_char_count(self, obj: Document) -> int:
        return len(obj.extracted_text or '')

    def get_file_url(self, obj: Document) -> str:
        request = self.context.get('request')
        if not obj.file:
            return ''
        url = obj.file.url
        if request:
            return request.build_absolute_uri(url)
        return url


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField(write_only=True)

    def validate_file(self, value):
        # Mantém a validação num só local (reutilizada pelo chat).
        try:
            value.open("rb")
            validate_pdf_upload(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

        return value

    def create(self, validated_data):
        request = self.context['request']
        uploaded = validated_data['file']
        original_name = get_valid_filename(
            os.path.basename(uploaded.name or 'document.pdf')
        )
        return Document.objects.create(
            user=request.user,
            original_name=original_name,
            file=uploaded,
        )


class DocumentIdsField(serializers.ListField):
    """Lista opcional de IDs de documentos do utilizador (deduplicada)."""

    def __init__(self, **kwargs):
        kwargs.setdefault('child', serializers.IntegerField(min_value=1))
        kwargs.setdefault('required', False)
        kwargs.setdefault('allow_null', True)
        kwargs.setdefault(
            'max_length',
            getattr(settings, 'RAG_MAX_FILTER_DOCUMENTS', 20),
        )
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        return normalize_document_ids(super().to_internal_value(data))


class RagAskRequestSerializer(serializers.Serializer):
    """POST /api/rag/ask/ — question obrigatória; document_ids opcional."""

    question = serializers.CharField(
        trim_whitespace=True,
        min_length=1,
        max_length=getattr(settings, 'RAG_MAX_QUESTION_LENGTH', 4000),
    )
    document_ids = DocumentIdsField()


class RagGenerateRequestSerializer(serializers.Serializer):
    """POST /api/rag/generate/ — gera material de estudo em Markdown."""

    kind = serializers.ChoiceField(
        choices=[
            ('summary', 'Resumo'),
            ('exercise_list', 'Lista de exercícios'),
            ('roadmap', 'Roadmap'),
        ]
    )
    title = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
        max_length=160,
    )
    topic = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
        max_length=getattr(settings, 'RAG_MAX_QUESTION_LENGTH', 4000),
    )
    instructions = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
        max_length=4000,
    )
    document_ids = DocumentIdsField()
