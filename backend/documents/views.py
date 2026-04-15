from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .extraction import extract_and_save_document
from .models import Document
from .serializers import DocumentDetailSerializer, DocumentUploadSerializer

# Apagar o documento
class DocumentDeleteView(APIView):
    
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        doc = get_object_or_404(Document, pk=pk, user=request.user)
        if doc.file:
            doc.file.delete(save=False)
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Listar os documentos
class DocumentListView(APIView):
   
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Document.objects.filter(user=request.user)
        serializer = DocumentDetailSerializer(
            qs, many=True, context={'request': request}
        )
        return Response(serializer.data)

# Upload de documento
class DocumentUploadView(APIView):
   
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request): # Upload de documento

        serializer = DocumentUploadSerializer( # Serializar o documento
            data=request.data,
            context={'request': request},
        )

        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        extract_and_save_document(document)
        document.refresh_from_db()
        out = DocumentDetailSerializer(document, context={'request': request})
        # Devolver o documento atualizado
        return Response(out.data, status=status.HTTP_201_CREATED)
