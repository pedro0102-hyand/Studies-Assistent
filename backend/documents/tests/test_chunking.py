import re

from django.test import SimpleTestCase

from documents.chunking import (
    chunks_with_indices,
    normalize_extracted_text,
    split_into_chunks,
)


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

    def test_normaliza_blocos_de_linhas_vazias(self) -> None:
        t = 'Resumo\n\n\n\n\nMais texto'
        self.assertEqual(normalize_extracted_text(t), 'Resumo\n\nMais texto')

    def test_fim_do_chunk_nao_parte_palavra_quando_ha_espaco_antes(self) -> None:
        # Palavras de 10 letras; o limite de tamanho não deve cortar «abcde» ao meio
        # se existir um espaço antes no mesmo segmento.
        toks = [f'abcde{x:03d}' for x in range(120)]
        text = ' '.join(toks)
        chunks = split_into_chunks(text, chunk_size=130, overlap=20)
        for c in chunks:
            for token in c.split():
                self.assertRegex(token, r'^abcde\d{3}$', msg=f'token partido: {token!r}')

    def test_corte_prefere_espaco(self) -> None:
        # Cada token é "palavraN"; nenhum chunk deve cortar a meio de um token
        parts = [f'palavra{n}' for n in range(80)]
        text = ' '.join(parts)
        chunks = split_into_chunks(text, chunk_size=120, overlap=15)
        self.assertGreater(len(chunks), 1)
        for c in chunks:
            for token in c.split():
                self.assertIsNotNone(
                    re.fullmatch(r'palavra\d+', token),
                    msg=f'token incompleto ou inválido: {token!r}',
                )
