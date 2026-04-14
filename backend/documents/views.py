from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Document
from .serializers import DocumentDetailSerializer, DocumentUploadSerializer


class DocumentDeleteView(APIView):
    """
    DELETE — remove o PDF do disco e o registo na BD.
    Só o dono do documento (404 se o id não existir ou for de outro utilizador).
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        
        doc = get_object_or_404(Document, pk=pk, user=request.user)
        if doc.file:
            doc.file.delete(save=False)
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# View for listing documents
class DocumentListView(APIView):
    """
    GET — lista PDFs do utilizador autenticado (nunca os de outros).
    """

    permission_classes = [IsAuthenticated] # Permission classes for the view

    def get(self, request):

        qs = Document.objects.filter(user=request.user) # Get the documents for the user
        ser = DocumentDetailSerializer(qs, many=True, context={'request': request}) # Serialize the documents
        return Response(ser.data)


# View for uploading a document
class DocumentUploadView(APIView):
    """
    POST multipart com campo `file` (PDF).
    Requer header: Authorization: Bearer <access_token>
    """

    permission_classes = [IsAuthenticated] # Permission classes for the view

    parser_classes = [MultiPartParser, FormParser] # Parser classes for the view

    def post(self, request):

        serializer = DocumentUploadSerializer(
            data=request.data,
            context={'request': request},

        )
        serializer.is_valid(raise_exception=True) # Validate the serializer
        document = serializer.save() # Save the document
        out = DocumentDetailSerializer(document, context={'request': request}) # Serialize the document
        return Response(out.data, status=status.HTTP_201_CREATED) # Return the response
