
from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from chat.models import Conversation, Message
from documents.ollama_chat import OllamaChatError

User = get_user_model()


class ChatSendMessageTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user('chatuser', 'chat@example.com', 'secret')
        self.conv = Conversation.objects.create(user=self.user, title='Teste')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('chat.views.run_rag_for_user')
    def test_post_grava_duas_mensagens(self, mock_rag) -> None:
        mock_rag.return_value = {
            'answer': 'Resposta do modelo.',
            'sources': [
                {
                    'document_id': 1,
                    'chunk_index': 0,
                    'original_name': 'a.pdf',
                    'excerpt': 'trecho',
                }
            ],
        }
        r = self.client.post(
            f'/api/chat/conversations/{self.conv.pk}/messages/',
            {'content': 'Qual é o tema?'},
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['assistant_message']['content'], 'Resposta do modelo.')
        self.assertEqual(len(r.data['assistant_message']['sources']), 1)
        mock_rag.assert_called_once_with(
            user_id=self.user.pk,
            question='Qual é o tema?',
            document_ids=None,
            attachment_context=None,
            attachment_filename=None,
        )
        self.assertEqual(Message.objects.filter(conversation=self.conv).count(), 2)
        roles = list(
            Message.objects.filter(conversation=self.conv).values_list('role', flat=True)
        )
        self.assertEqual(roles, ['user', 'assistant'])

    @patch('chat.views.run_rag_for_user')
    def test_post_rag_falha_mantem_mensagem_utilizador(self, mock_rag) -> None:
        mock_rag.side_effect = OllamaChatError('modelo indisponível')
        r = self.client.post(
            f'/api/chat/conversations/{self.conv.pk}/messages/',
            {'content': 'Pergunta que fica no histórico'},
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertIn('user_message', r.data)
        self.assertEqual(r.data['user_message']['role'], 'user')
        self.assertEqual(r.data['user_message']['content'], 'Pergunta que fica no histórico')
        msgs = list(Message.objects.filter(conversation=self.conv))
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].role, Message.Role.USER)

    def test_get_mensagens_vazio(self) -> None:
        r = self.client.get(f'/api/chat/conversations/{self.conv.pk}/messages/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['results'], [])
        self.assertEqual(r.data['count'], 0)

    def test_post_sem_conteudo_400(self) -> None:
        r = self.client.post(
            f'/api/chat/conversations/{self.conv.pk}/messages/',
            {},
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
