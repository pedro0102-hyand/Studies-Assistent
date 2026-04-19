"""Etapa 5.4 — build_context_from_chunks."""
from django.test import SimpleTestCase, override_settings

from documents.rag import build_context_from_chunks


class BuildContextTests(SimpleTestCase):
    def test_chunks_vazios(self) -> None:
        ctx, sources = build_context_from_chunks([])
        self.assertEqual(ctx, '')
        self.assertEqual(sources, [])

    def test_um_chunk_com_etiqueta(self) -> None:
        chunks = [
            {
                'document': 'Texto do chunk.',
                'metadata': {
                    'document_id': 1,
                    'chunk_index': 0,
                    'original_name': 'a.pdf',
                },
            }
        ]
        ctx, sources = build_context_from_chunks(chunks, max_chars=5000)
        self.assertIn('[fonte: a.pdf, chunk 0]', ctx)
        self.assertIn('Texto do chunk.', ctx)
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]['document_id'], 1)
        self.assertEqual(sources[0]['chunk_index'], 0)
        self.assertEqual(sources[0]['original_name'], 'a.pdf')
        self.assertIn('Texto', sources[0]['excerpt'])

    def test_sem_etiquetas(self) -> None:
        chunks = [
            {
                'document': 'Só corpo.',
                'metadata': {'document_id': 2, 'chunk_index': 1, 'original_name': 'b.pdf'},
            }
        ]
        ctx, sources = build_context_from_chunks(
            chunks, max_chars=100, label_sources=False
        )
        self.assertEqual(ctx, 'Só corpo.')
        self.assertNotIn('[fonte:', ctx)

    def test_respeita_max_chars(self) -> None:
        chunks = [
            {
                'document': 'A' * 100,
                'metadata': {'document_id': 1, 'chunk_index': 0, 'original_name': 'x.pdf'},
            }
        ]
        ctx, sources = build_context_from_chunks(chunks, max_chars=50, label_sources=False)
        self.assertLessEqual(len(ctx), 50)
        self.assertTrue(ctx.endswith('…') or len(ctx) == 50)

    def test_varios_chunks_separador(self) -> None:
        chunks = [
            {
                'document': 'um',
                'metadata': {'document_id': 1, 'chunk_index': 0, 'original_name': 'a.pdf'},
            },
            {
                'document': 'dois',
                'metadata': {'document_id': 1, 'chunk_index': 1, 'original_name': 'a.pdf'},
            },
        ]
        ctx, _ = build_context_from_chunks(chunks, max_chars=500, label_sources=False)
        self.assertIn('\n\n---\n\n', ctx)
        self.assertIn('um', ctx)
        self.assertIn('dois', ctx)

    @override_settings(RAG_MAX_CONTEXT_CHARS=300)
    def test_usa_settings_quando_max_chars_none(self) -> None:
        chunks = [
            {
                'document': 'x' * 500,
                'metadata': {'document_id': 1, 'chunk_index': 0, 'original_name': 'z.pdf'},
            }
        ]
        ctx, _ = build_context_from_chunks(chunks, max_chars=None, label_sources=False)
        self.assertLessEqual(len(ctx), 300)
