from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import DocumentDetailSerializer, DocumentUploadSerializer 

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
