"""Etapa 5.8 — erros HTTP e throttling do endpoint RAG."""
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from documents.ollama_chat import OllamaChatError
from documents.ollama_embed import OllamaEmbedError
from documents.views import RagAskView

User = get_user_model()


class RagAskErrorAndThrottleTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user('t502', '502@example.com', 'x')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('documents.views.run_rag_for_user', side_effect=OllamaEmbedError('embed falhou'))
    def test_502_embedding(self, _mock) -> None:
        r = self.client.post('/api/rag/ask/', {'question': 'Q?'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertIsNotNone(r.data.get('detail'))

    @patch('documents.views.run_rag_for_user', side_effect=OllamaChatError('chat falhou'))
    def test_502_chat(self, _mock) -> None:
        r = self.client.post('/api/rag/ask/', {'question': 'Q?'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_502_BAD_GATEWAY)

    def test_throttle_scope_configurado(self) -> None:
        self.assertEqual(RagAskView.throttle_scope, 'rag')
        self.assertTrue(RagAskView.throttle_classes)

    def test_settings_tem_taxa_rag(self) -> None:
        rates = settings.REST_FRAMEWORK.get('DEFAULT_THROTTLE_RATES') or {}
        self.assertIn('rag', rates)
