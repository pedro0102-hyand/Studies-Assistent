from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from documents import chroma_index as chroma_index_mod


class DeleteChromaTests(SimpleTestCase):
    def tearDown(self) -> None:
        chroma_index_mod.reset_chroma_singleton_for_tests()

    @patch.object(chroma_index_mod, '_get_collection')
    def test_delete_usa_where_document_id(self, mock_get) -> None:
        coll = MagicMock()
        mock_get.return_value = coll
        chroma_index_mod.delete_chroma_for_document(42)
        coll.delete.assert_called_once_with(where={'document_id': 42})

    def test_delete_id_invalido_nao_chama(self) -> None:
        with patch.object(chroma_index_mod, '_get_collection') as mock_get:
            chroma_index_mod.delete_chroma_for_document(0)
            mock_get.assert_not_called()
