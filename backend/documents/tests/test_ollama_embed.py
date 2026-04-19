from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from documents.ollama_embed import OllamaEmbedError, embed_query, embed_texts, vector_summary


class VectorSummaryTests(SimpleTestCase):

    def test_vazio(self) -> None:
        s = vector_summary([])
        self.assertEqual(s['dim'], 0)
        self.assertEqual(s['l2'], 0.0)

    def test_vetor_simples(self) -> None:

        s = vector_summary([0.0, 3.0, 4.0])
        self.assertEqual(s['dim'], 3)
        self.assertAlmostEqual(s['l2'], 5.0)
        self.assertAlmostEqual(s['mean'], 7.0 / 3.0)


class EmbedTextsMockedTests(SimpleTestCase):
    """embed_texts sem rede — httpx.Client simulado."""

    def test_embed_texts_devolve_vetores(self) -> None:

        fake_emb = [[0.1, -0.2, 0.3], [0.0, 1.0, 0.0]]
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {'embeddings': fake_emb}

        client_inst = MagicMock()
        client_inst.post.return_value = resp

        with patch('documents.ollama_embed.httpx.Client') as mock_cls:
            mock_cls.return_value.__enter__.return_value = client_inst
            mock_cls.return_value.__exit__.return_value = None

            out = embed_texts(
                ['a', 'b'],
                base_url='http://127.0.0.1:11434',
                model='nomic-embed-text:latest',
            )

        self.assertEqual(len(out), 2)
        self.assertEqual(len(out[0]), 3)
        self.assertAlmostEqual(out[1][1], 1.0)
        client_inst.post.assert_called_once()
        args, kwargs = client_inst.post.call_args
        self.assertIn('/api/embed', args[0])
        self.assertEqual(kwargs['json']['input'], ['a', 'b'])

    def test_http_erro_levanta_ollama_embed_error(self) -> None:

        resp = MagicMock()
        resp.status_code = 500
        resp.text = 'fail'
        resp.reason_phrase = 'ERR'
        resp.json.side_effect = ValueError

        client_inst = MagicMock()
        client_inst.post.return_value = resp

        with patch('documents.ollama_embed.httpx.Client') as mock_cls:

            mock_cls.return_value.__enter__.return_value = client_inst
            mock_cls.return_value.__exit__.return_value = None

            with self.assertRaises(OllamaEmbedError):
                embed_texts(
                    ['x'],
                    base_url='http://127.0.0.1:11434',
                    model='m',
                )


class EmbedQueryTests(SimpleTestCase):
    
    def test_texto_vazio_levanta_value_error(self) -> None:
        with self.assertRaises(ValueError):
            embed_query('', base_url='http://127.0.0.1:11434', model='m')
        with self.assertRaises(ValueError):
            embed_query('   \n\t', base_url='http://127.0.0.1:11434', model='m')

    def test_devolve_um_vetor(self) -> None:
        fake_emb = [[0.1, -0.2, 0.3]]
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {'embeddings': fake_emb}

        client_inst = MagicMock()
        client_inst.post.return_value = resp

        with patch('documents.ollama_embed.httpx.Client') as mock_cls:
            mock_cls.return_value.__enter__.return_value = client_inst
            mock_cls.return_value.__exit__.return_value = None

            out = embed_query(
                'Qual é o tema?',
                base_url='http://127.0.0.1:11434',
                model='nomic-embed-text:latest',
            )

        self.assertEqual(len(out), 3)
        self.assertAlmostEqual(out[0], 0.1)
        kwargs = client_inst.post.call_args[1]['json']
        self.assertEqual(kwargs['input'], ['Qual é o tema?'])
