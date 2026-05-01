from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from core.pagination import DocumentListPagination

from .chroma_index import delete_chroma_for_document
from .models import Document
from .ollama_chat import OllamaChatError
from .ollama_embed import OllamaEmbedError
from .rag import run_rag_for_user, run_rag_generate_for_user
from .serializers import (
    DocumentDetailSerializer,
    DocumentUploadSerializer,
    RagAskRequestSerializer,
    RagGenerateRequestSerializer,
)
from .tasks import process_document_extraction
from django.conf import settings
import threading


class DocumentDetailView(APIView):
    """GET um documento (polling de estado) ou DELETE."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        doc = get_object_or_404(Document, pk=pk, user=request.user)
        return Response(
            DocumentDetailSerializer(doc, context={'request': request}).data,
        )

    def delete(self, request, pk):
        doc = get_object_or_404(Document, pk=pk, user=request.user)
        delete_chroma_for_document(doc.pk)
        if doc.file:
            doc.file.delete(save=False)
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Listar os documentos
class DocumentListView(APIView):
   
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Document.objects.filter(user=request.user)
        paginator = DocumentListPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = DocumentDetailSerializer(
            page, many=True, context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)

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
        # Enfileira para Celery; em DEBUG sem Redis, pode falhar — faz fallback sem bloquear request.
        try:
            process_document_extraction.delay(document.pk)
        except Exception:
            if getattr(settings, 'DEBUG', False):
                threading.Thread(
                    target=process_document_extraction,
                    args=(document.pk,),
                    daemon=True,
                ).start()
            else:
                # Em produção, expõe falha de infraestrutura em vez de fingir sucesso.
                return Response(
                    {'detail': 'Fila de processamento indisponível (Celery/Redis).'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
        document.refresh_from_db()
        out = DocumentDetailSerializer(document, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)


class RagAskView(APIView):
    """POST /api/rag/ask/ — RAG com JWT; corpo: question, document_ids opcional."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'rag'

    def post(self, request):
        serializer = RagAskRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data['question']
        document_ids = serializer.validated_data.get('document_ids')

        if document_ids is not None:
            found = set(
                Document.objects.filter(
                    user=request.user, pk__in=document_ids
                ).values_list('pk', flat=True)
            )
            if set(document_ids) != found:
                return Response(
                    {
                        'detail': 'Um ou mais document_ids são inválidos ou não pertencem ao utilizador.',
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            payload = run_rag_for_user(
                user_id=request.user.pk,
                question=question,
                document_ids=document_ids,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except OllamaEmbedError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except OllamaChatError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except RuntimeError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(payload, status=status.HTTP_200_OK)


class RagGenerateView(APIView):
    """POST /api/rag/generate/ — gera materiais (Markdown) baseados no RAG."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'rag'

    def post(self, request):
        serializer = RagGenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        kind = serializer.validated_data['kind']
        title = serializer.validated_data.get('title') or ''
        topic = serializer.validated_data.get('topic') or ''
        instructions = serializer.validated_data.get('instructions') or ''
        document_ids = serializer.validated_data.get('document_ids')

        if document_ids is not None:
            found = set(
                Document.objects.filter(
                    user=request.user, pk__in=document_ids
                ).values_list('pk', flat=True)
            )
            if set(document_ids) != found:
                return Response(
                    {
                        'detail': 'Um ou mais document_ids são inválidos ou não pertencem ao utilizador.',
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            payload = run_rag_generate_for_user(
                user_id=request.user.pk,
                kind=kind,
                title=title,
                topic=topic,
                instructions=instructions,
                document_ids=document_ids,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except OllamaEmbedError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except OllamaChatError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except RuntimeError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(payload, status=status.HTTP_200_OK)
