"""Etapa 6.5 — API de conversas (listar, criar, apagar, isolamento por utilizador)."""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from chat.models import Conversation

User = get_user_model()


class ChatConversationsApiTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user('c6', 'c6@example.com', 'secret')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_lista_vazia(self) -> None:
        r = self.client.get('/api/chat/conversations/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['results'], [])
        self.assertEqual(r.data['count'], 0)

    def test_criar_e_listar(self) -> None:
        r = self.client.post(
            '/api/chat/conversations/',
            {'title': 'Estudo'},
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['title'], 'Estudo')
        rid = r.data['id']

        r2 = self.client.get('/api/chat/conversations/')
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r2.data['results']), 1)
        self.assertEqual(r2.data['results'][0]['id'], rid)

    def test_apagar_conversa(self) -> None:
        c = Conversation.objects.create(user=self.user, title='x')
        r = self.client.delete(f'/api/chat/conversations/{c.pk}/')
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Conversation.objects.filter(pk=c.pk).exists())

    def test_nao_autenticado_401(self) -> None:
        client = APIClient()
        r = client.get('/api/chat/conversations/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_outro_utilizador_404(self) -> None:
        other = User.objects.create_user('outro6', 'o6@example.com', 'x')
        c = Conversation.objects.create(user=other, title='privada')
        r = self.client.get(f'/api/chat/conversations/{c.pk}/messages/')
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)
