"""Etapa 5.5 — generate_rag_answer."""
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from documents.ollama_chat import OllamaChatError
from documents.rag import generate_rag_answer


class GenerateRagAnswerTests(SimpleTestCase):
    @patch('documents.ollama_chat.ollama_chat_completion', return_value='Resposta.')
    def test_chama_chat_com_system_e_user(self, mock_chat) -> None:
        out = generate_rag_answer('Contexto A.', 'O que diz?')
        self.assertEqual(out, 'Resposta.')
        mock_chat.assert_called_once()
        msgs = mock_chat.call_args[0][0]
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]['role'], 'system')
        self.assertEqual(msgs[1]['role'], 'user')
        self.assertIn('Contexto A.', msgs[1]['content'])
        self.assertIn('O que diz?', msgs[1]['content'])

    def test_pergunta_vazia(self) -> None:
        with self.assertRaises(ValueError):
            generate_rag_answer('ctx', '   ')

    @patch('documents.ollama_chat.ollama_chat_completion', side_effect=OllamaChatError('x'))
    def test_erro_envolvido(self, _mock) -> None:
        with self.assertRaises(OllamaChatError) as ctx:
            generate_rag_answer('c', 'p?')
        self.assertIn('modelo de chat', str(ctx.exception).lower())

    @override_settings(
        OLLAMA_BASE_URL='http://h:1',
        OLLAMA_CHAT_MODEL='mini:latest',
        OLLAMA_CHAT_TIMEOUT=30.0,
    )
    @patch('documents.ollama_chat.ollama_chat_completion', return_value='ok')
    def test_passa_settings_ao_chat(self, mock_chat) -> None:
        generate_rag_answer('x', 'y')
        kw = mock_chat.call_args[1]
        self.assertEqual(kw['base_url'], 'http://h:1')
        self.assertEqual(kw['model'], 'mini:latest')
        self.assertEqual(kw['timeout'], 30.0)
