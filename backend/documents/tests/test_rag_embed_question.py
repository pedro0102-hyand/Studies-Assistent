"""Etapa 5.2 — embed_question (settings + mensagem de erro)."""
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from documents.ollama_embed import OllamaEmbedError
from documents.rag import embed_question


class EmbedQuestionSettingsTests(SimpleTestCase):
    def test_usa_ollama_embed_query_com_parametros_das_settings(self) -> None:
        with patch('documents.ollama_embed.embed_query', return_value=[1.0, 2.0]) as mock_eq:
            with override_settings(
                OLLAMA_BASE_URL='http://x:11434',
                OLLAMA_EMBED_MODEL='meu-modelo:latest',
                OLLAMA_EMBED_TIMEOUT=99.0,
            ):
                out = embed_question('  Olá?  ')
        self.assertEqual(out, [1.0, 2.0])
        mock_eq.assert_called_once()
        _, kwargs = mock_eq.call_args
        self.assertEqual(kwargs['base_url'], 'http://x:11434')
        self.assertEqual(kwargs['model'], 'meu-modelo:latest')
        self.assertEqual(kwargs['timeout'], 99.0)
        self.assertEqual(mock_eq.call_args[0][0], 'Olá?')

    def test_erro_ollama_envolve_mensagem_clara(self) -> None:
        inner = OllamaEmbedError('connection refused')
        with patch('documents.ollama_embed.embed_query', side_effect=inner):
            with self.assertRaises(OllamaEmbedError) as ctx:
                embed_question('teste')
        msg = str(ctx.exception)
        self.assertIn('embedding da pergunta', msg.lower())
        self.assertIn('connection refused', msg.lower())
