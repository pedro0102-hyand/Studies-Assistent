"""Etapa 5.3 — search_similar_chunks (Chroma + filtro user_id)."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from documents import chroma_index as chroma_index_mod


class SearchSimilarChunksTests(SimpleTestCase):

    def tearDown(self) -> None:
        chroma_index_mod.reset_chroma_singleton_for_tests()

    def test_user_id_invalido(self) -> None:

        with self.assertRaises(ValueError):
            chroma_index_mod.search_similar_chunks([0.1], user_id=0)

    def test_embedding_vazio(self) -> None:

        with self.assertRaises(ValueError):
            chroma_index_mod.search_similar_chunks([], user_id=1)

    @patch.object(chroma_index_mod, '_get_collection')
    def test_filtro_obrigatorio_user_id(self, mock_get) -> None:
        coll = MagicMock()
        coll.query.return_value = {
            'documents': [['texto a']],
            'metadatas': [[{'document_id': 7, 'chunk_index': 0, 'user_id': 3}]],
            'distances': [[0.5]],
        }
        mock_get.return_value = coll

        out = chroma_index_mod.search_similar_chunks([0.0, 1.0], user_id=3, top_k=4)

        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]['document'], 'texto a')
        self.assertEqual(out[0]['metadata'].get('document_id'), 7)
        self.assertEqual(out[0]['distance'], 0.5)
        coll.query.assert_called_once()
        kw = coll.query.call_args[1]
        self.assertEqual(kw['where'], {'user_id': 3})
        self.assertEqual(kw['n_results'], 4)
        self.assertEqual(kw['query_embeddings'], [[0.0, 1.0]])

    @patch.object(chroma_index_mod, '_get_collection')
    def test_filtro_opcional_document_ids(self, mock_get) -> None:
        coll = MagicMock()
        coll.query.return_value = {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
        mock_get.return_value = coll

        chroma_index_mod.search_similar_chunks(
            [0.1],
            user_id=2,
            top_k=5,
            document_ids=[10, 20],
        )

        kw = coll.query.call_args[1]
        self.assertEqual(
            kw['where'],
            {'$and': [{'user_id': 2}, {'document_id': {'$in': [10, 20]}}]},
        )

    @override_settings(RAG_TOP_K=7)
    @patch.object(chroma_index_mod, '_get_collection')
    def test_top_k_default_settings(self, mock_get) -> None:
        coll = MagicMock()
        coll.query.return_value = {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
        mock_get.return_value = coll

        chroma_index_mod.search_similar_chunks([0.1], user_id=1)

        self.assertEqual(coll.query.call_args[1]['n_results'], 7)

    @patch.object(chroma_index_mod, '_get_collection')
    def test_resultado_vazio(self, mock_get) -> None:
        coll = MagicMock()
        coll.query.return_value = {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
        mock_get.return_value = coll

        out = chroma_index_mod.search_similar_chunks([0.1], user_id=1)
        self.assertEqual(out, [])

    @patch.object(chroma_index_mod, '_get_collection')
    def test_chroma_erro_runtime(self, mock_get) -> None:
        coll = MagicMock()
        coll.query.side_effect = OSError('disk')
        mock_get.return_value = coll

        with self.assertRaises(RuntimeError):
            chroma_index_mod.search_similar_chunks([0.1], user_id=1)


class WhereRagUnitTests(SimpleTestCase):

    def test_where_só_user(self) -> None:

        w = chroma_index_mod._where_rag(5, None)
        self.assertEqual(w, {'user_id': 5})

    def test_where_com_ids(self) -> None:
        
        w = chroma_index_mod._where_rag(5, [1, 2])
        self.assertEqual(
            w,
            {'$and': [{'user_id': 5}, {'document_id': {'$in': [1, 2]}}]},
        )
