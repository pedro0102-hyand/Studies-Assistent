import os
from django.utils.text import get_valid_filename
from rest_framework import serializers
from .models import Document

PDF_MAGIC = b'%PDF' # Magic number for PDF files
MAX_PDF_BYTES = 25 * 1024 * 1024  # 25 MB  Maximum size for PDF files

# Serializer for Document detail
class DocumentDetailSerializer(serializers.ModelSerializer):
    

    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ('id', 'original_name', 'file_url', 'created_at', 'updated_at')
        read_only_fields = fields

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
