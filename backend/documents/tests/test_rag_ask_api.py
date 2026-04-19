"""Etapa 5.6 — POST /api/rag/ask/."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


class RagAskApiTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user('raguser', 'rag@example.com', 'secret')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('documents.views.run_rag_for_user')
    def test_post_sucesso(self, mock_run) -> None:
        mock_run.return_value = {
            'answer': 'Resposta.',
            'sources': [
                {
                    'document_id': 1,
                    'chunk_index': 0,
                    'original_name': 'a.pdf',
                    'excerpt': 'trecho',
                }
            ],
        }
        response = self.client.post(
            '/api/rag/ask/',
            {'question': 'O que diz o PDF?'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['answer'], 'Resposta.')
        self.assertEqual(len(response.data['sources']), 1)
        mock_run.assert_called_once_with(
            user_id=self.user.pk,
            question='O que diz o PDF?',
            document_ids=None,
        )

    def test_sem_autenticacao(self) -> None:
        client = APIClient()
        response = client.post('/api/rag/ask/', {'question': 'x'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_question_em_falta(self) -> None:
        response = self.client.post('/api/rag/ask/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_document_ids_invalidos(self) -> None:
        with patch('documents.views.Document.objects.filter') as m_filter:
            m_filter.return_value.values_list.return_value = []
            response = self.client.post(
                '/api/rag/ask/',
                {'question': 'Q?', 'document_ids': [99999]},
                format='json',
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        detail = str(response.data.get('detail', ''))
        self.assertIn('document_ids', detail.lower())

    @patch('documents.views.run_rag_for_user', side_effect=RuntimeError('índice indisponível'))
    def test_erro_chroma_503(self, _mock) -> None:
        response = self.client.post(
            '/api/rag/ask/', {'question': 'Q?'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

