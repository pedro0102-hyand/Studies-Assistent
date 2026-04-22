from django.urls import path

from . import views

urlpatterns = [
    path(
        'chat/conversations/',
        views.ConversationListCreateView.as_view(),
        name='chat_conversation_list',
    ),
    path(
        'chat/conversations/<int:pk>/',
        views.ConversationDetailDeleteView.as_view(),
        name='chat_conversation_delete',
    ),
    path(
        'chat/conversations/<int:pk>/messages/',
        views.ConversationMessagesView.as_view(),
        name='chat_conversation_messages',
    ),
]
