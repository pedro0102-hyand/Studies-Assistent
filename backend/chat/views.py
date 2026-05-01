from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from core.pagination import ConversationListPagination, MessageListPagination

from documents.models import Document
from documents.ollama_chat import OllamaChatError
from documents.ollama_embed import OllamaEmbedError
from documents.rag import run_rag_for_user

from .models import Conversation, Message
from .serializers import (
    ChatSendSerializer,
    ConversationCreateSerializer,
    ConversationSerializer,
    MessageSerializer,
)


class ConversationListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'chat'

    def get(self, request):
        qs = Conversation.objects.filter(user=request.user)
        paginator = ConversationListPagination()
        page = paginator.paginate_queryset(qs, request)
        ser = ConversationSerializer(page, many=True)
        return paginator.get_paginated_response(ser.data)

    def post(self, request):
        ser = ConversationCreateSerializer(data=request.data, context={'request': request})
        ser.is_valid(raise_exception=True)
        conv = ser.save()
        out = ConversationSerializer(conv)
        return Response(out.data, status=status.HTTP_201_CREATED)


class ConversationDetailDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'chat'

    def delete(self, request, pk):
        conv = get_object_or_404(Conversation, pk=pk, user=request.user)
        conv.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def patch(self, request, pk):
        """Renomeia uma conversa (PATCH { "title": "novo nome" })."""
        conv = get_object_or_404(Conversation, pk=pk, user=request.user)
        title = (request.data.get('title') or '').strip()
        if not title:
            return Response({'detail': 'O título não pode ser vazio.'}, status=status.HTTP_400_BAD_REQUEST)
        title = title[:255]
        Conversation.objects.filter(pk=conv.pk).update(title=title)
        conv.refresh_from_db()
        out = ConversationSerializer(conv)
        return Response(out.data)


class ConversationMessagesView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'chat'

    def get(self, request, pk):
        conv = get_object_or_404(Conversation, pk=pk, user=request.user)
        qs = conv.messages.all()
        paginator = MessageListPagination()
        page = paginator.paginate_queryset(qs, request)
        ser = MessageSerializer(page, many=True)
        return paginator.get_paginated_response(ser.data)

    def post(self, request, pk):
        conv = get_object_or_404(Conversation, pk=pk, user=request.user)
        ser = ChatSendSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        content = ser.validated_data['content']
        document_ids = ser.validated_data.get('document_ids')

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

        now = timezone.now()
        with transaction.atomic():
            user_msg = Message.objects.create(
                conversation=conv,
                role=Message.Role.USER,
                content=content,
            )
            conv_updates: dict = {'updated_at': now}
            if not (conv.title or '').strip():
                stripped = content.strip()
                title = stripped[:80]
                if len(stripped) > 80:
                    title += '…'
                conv_updates['title'] = title
            Conversation.objects.filter(pk=conv.pk).update(**conv_updates)

        def _err(detail: str, code: int, *, user_msg_for_body: Message | None = None):
            body: dict = {'detail': detail}
            if user_msg_for_body is not None:
                body['user_message'] = MessageSerializer(user_msg_for_body).data
            return Response(body, status=code)

        try:
            payload = run_rag_for_user(
                user_id=request.user.pk,
                question=content,
                document_ids=document_ids,
            )
        except ValueError as exc:
            return _err(str(exc), status.HTTP_400_BAD_REQUEST, user_msg_for_body=user_msg)
        except OllamaEmbedError as exc:
            return _err(str(exc), status.HTTP_502_BAD_GATEWAY, user_msg_for_body=user_msg)
        except OllamaChatError as exc:
            return _err(str(exc), status.HTTP_502_BAD_GATEWAY, user_msg_for_body=user_msg)
        except RuntimeError as exc:
            return _err(str(exc), status.HTTP_503_SERVICE_UNAVAILABLE, user_msg_for_body=user_msg)

        with transaction.atomic():
            assistant_msg = Message.objects.create(
                conversation=conv,
                role=Message.Role.ASSISTANT,
                content=payload.get('answer') or '',
                sources=payload.get('sources') or [],
            )
            Conversation.objects.filter(pk=conv.pk).update(updated_at=timezone.now())

        return Response(
            {
                'user_message': MessageSerializer(user_msg).data,
                'assistant_message': MessageSerializer(assistant_msg).data,
            },
            status=status.HTTP_201_CREATED,
        )
