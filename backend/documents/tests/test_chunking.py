from django.test import SimpleTestCase

from documents.chunking import chunks_with_indices, split_into_chunks


class SplitIntoChunksTests(SimpleTestCase):

    def test_texto_vazio_devolve_lista_vazia(self) -> None:

        self.assertEqual(split_into_chunks(''), [])
        self.assertEqual(split_into_chunks('   '), [])

    def test_um_só_chunk_quando_texto_cabe_no_tamanho(self) -> None:

        text = 'a' * 50
        chunks = split_into_chunks(text, chunk_size=200, overlap=20)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text)

    def test_varios_chunks_com_overlap(self) -> None:

        # 300 chars: com chunk 100 e overlap 10 → passo 90
        text = 'a' * 100 + 'b' * 100 + 'c' * 100
        chunks = split_into_chunks(text, chunk_size=100, overlap=10)
        self.assertGreaterEqual(len(chunks), 3)
        joined = ''.join(chunks)
        self.assertIn('a', joined)
        self.assertIn('c', joined)

    def test_chunk_size_minimo_100(self) -> None:

        text = 'x' * 250
        chunks = split_into_chunks(text, chunk_size=50, overlap=5)
        # 50 é elevado a 100
        self.assertTrue(all(len(c) <= 100 for c in chunks))

    def test_chunks_with_indices(self) -> None:
        
        text = 'alfa beta'
        rows = chunks_with_indices(text, document_id=42, chunk_size=100, overlap=10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['document_id'], 42)
        self.assertEqual(rows[0]['chunk_index'], 0)
        self.assertEqual(rows[0]['text'], 'alfa beta')
