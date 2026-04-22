from django.conf import settings
from rest_framework import serializers

from .models import Conversation, Message


class ConversationSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ('id', 'title', 'created_at', 'updated_at', 'message_count')
        read_only_fields = fields

    def get_message_count(self, obj: Conversation) -> int:
        return obj.messages.count()


class ConversationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ('title',)

    def create(self, validated_data):
        request = self.context['request']
        return Conversation.objects.create(user=request.user, **validated_data)


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('id', 'role', 'content', 'sources', 'created_at')
        read_only_fields = fields


class ChatSendSerializer(serializers.Serializer):
    """Corpo POST …/messages/ — igual ao RAG quanto a limites."""

    content = serializers.CharField(
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
        seen: set[int] = set()
        out: list[int] = []
        for x in value:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out
