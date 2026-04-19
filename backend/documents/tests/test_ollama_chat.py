
from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase
from documents.ollama_chat import OllamaChatError, ollama_chat_completion


class OllamaChatCompletionTests(SimpleTestCase):

    def test_devolve_conteudo_do_assistant(self) -> None:

        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            'message': {'role': 'assistant', 'content': '  Olá.  '},
            'done': True,
        }

        client_inst = MagicMock()
        client_inst.post.return_value = resp

        with patch('documents.ollama_chat.httpx.Client') as mock_cls:

            mock_cls.return_value.__enter__.return_value = client_inst
            mock_cls.return_value.__exit__.return_value = None

            out = ollama_chat_completion(
                [{'role': 'user', 'content': 'x'}],
                base_url='http://127.0.0.1:11434',
                model='gemma2:2b',
            )

        self.assertEqual(out, 'Olá.')
        args, kwargs = client_inst.post.call_args
        self.assertIn('/api/chat', args[0])
        self.assertFalse(kwargs['json']['stream'])

    def test_http_erro(self) -> None:

        resp = MagicMock()
        resp.status_code = 500
        resp.text = 'fail'
        resp.json.side_effect = ValueError
        client_inst = MagicMock()
        client_inst.post.return_value = resp

        with patch('documents.ollama_chat.httpx.Client') as mock_cls:

            mock_cls.return_value.__enter__.return_value = client_inst
            mock_cls.return_value.__exit__.return_value = None

            with self.assertRaises(OllamaChatError):

                ollama_chat_completion(
                    [{'role': 'user', 'content': 'x'}],
                    base_url='http://127.0.0.1:11434',
                    model='m',
                )

    def test_messages_vazio(self) -> None:

        with self.assertRaises(ValueError):
            
            ollama_chat_completion([], base_url='http://x', model='m')
