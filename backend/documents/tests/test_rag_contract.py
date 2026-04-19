"""Etapa 5.1 — validação do contrato JSON do RAG."""
from django.conf import settings
from django.test import SimpleTestCase

from documents.serializers import (
    RagAskRequestSerializer,
    RagAskResponseSerializer,
    RagSourceSerializer,
)


class RagAskRequestSerializerTests(SimpleTestCase):

    def test_question_obrigatoria(self) -> None:

        s = RagAskRequestSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn('question', s.errors)

    def test_question_demasiado_longa(self) -> None:

        limit = getattr(settings, 'RAG_MAX_QUESTION_LENGTH', 4000)
        s = RagAskRequestSerializer(data={'question': 'x' * (limit + 1)})
        self.assertFalse(s.is_valid())

    def test_document_ids_opcional_e_deduplica(self) -> None:

        s = RagAskRequestSerializer(
            data={'question': 'Olá?', 'document_ids': [3, 3, 1, 2]}
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data['document_ids'], [3, 1, 2])

    def test_document_ids_vazio_equivale_a_omitir(self) -> None:
        
        s = RagAskRequestSerializer(data={'question': 'x', 'document_ids': []})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertIsNone(s.validated_data.get('document_ids'))


class RagResponseSerializerTests(SimpleTestCase):
    def test_resposta_minima(self) -> None:
        s = RagAskResponseSerializer(data={'answer': 'Resposta.'})
        self.assertTrue(s.is_valid(), s.errors)

    def test_resposta_com_fontes(self) -> None:
        payload = {
            'answer': 'Sim.',
            'sources': [
                {
                    'document_id': 1,
                    'chunk_index': 0,
                    'original_name': 'a.pdf',
                    'excerpt': 'Trecho...',
                }
            ],
        }
        s = RagAskResponseSerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)

    def test_fonte_invalida(self) -> None:
        s = RagSourceSerializer(
            data={
                'document_id': 1,
                'chunk_index': -1,
                'original_name': 'a.pdf',
                'excerpt': 'x',
            }
        )
        self.assertFalse(s.is_valid())
