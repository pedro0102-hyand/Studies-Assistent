
from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from documents.chunking import split_into_chunks
from documents.models import Document


class Command(BaseCommand):

    help = 'Lista os chunks (Etapa 4.3) recalculados a partir de `extracted_text` do documento.'

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            'document_id',
            nargs='?',
            type=int,
            default=None,
            help='ID primário do Document na base de dados',
        )
        parser.add_argument(
            '--list',
            '-l',
            action='store_true',
            help='Listar documentos (id, utilizador, caracteres extraídos, nome)',
        )
        parser.add_argument(
            '--preview',
            type=int,
            default=200,
            metavar='N',
            help='Caracteres de pré-visualização por chunk (0 = texto completo; predefinição: 200)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            metavar='M',
            help='Mostrar no máximo M chunks',
        )

    def _print_document_table(self) -> None:
        total = Document.objects.count()
        if total == 0:
            self.stdout.write(
                self.style.WARNING(
                    'Não há nenhum documento. Envia um PDF pela app (área PDFs) ou cria um no admin.'
                )
            )
            return

        self.stdout.write(f'Documentos na base de dados: {total} (até 50, mais recentes primeiro)\n')
        qs = Document.objects.order_by('-id')[:50]
        for d in qs:
            chars = len(d.extracted_text or '')
            chroma = 'sim' if d.chroma_indexed_at else ('erro' if d.chroma_error else '—')
            self.stdout.write(
                f'  id={d.pk!s:<5} user_id={d.user_id!s:<4} chars={chars!s:<7} '
                f'chunks={d.chunk_count!s:<4} chroma={chroma!s:<5} {d.original_name!r}'
            )

    def handle(self, *args, **options) -> None:
        if options['list']:
            self._print_document_table()
            return

        doc_id = options['document_id']
        if doc_id is None:
            raise CommandError(
                'Indica o id do documento (ex.: show_chunks 3) ou lista os ids com: show_chunks --list'
            )

        preview: int = options['preview']
        limit = options['limit']

        try:
            doc = Document.objects.get(pk=doc_id)
        except Document.DoesNotExist:
            self._print_document_table()
            self.stdout.flush()
            raise CommandError(
                f'Document id={doc_id} não existe. Usa um id da lista acima ou envia um PDF pela app.'
            )

        text = doc.extracted_text or ''
        if not text.strip():
            self.stdout.write(self.style.WARNING('Sem texto extraído (extracted_text vazio).'))
            return

        chunks = split_into_chunks(
            text,
            chunk_size=getattr(settings, 'RAG_CHUNK_SIZE', 1500),
            overlap=getattr(settings, 'RAG_CHUNK_OVERLAP', 200),
        )

        self.stdout.write(
            f'Document #{doc.pk} — {doc.original_name!r} — user_id={doc.user_id}'
        )
        self.stdout.write(
            f'Caracteres: {len(text)} · Chunks: {len(chunks)} '
            f'(RAG_CHUNK_SIZE={getattr(settings, "RAG_CHUNK_SIZE", 1500)}, '
            f'RAG_CHUNK_OVERLAP={getattr(settings, "RAG_CHUNK_OVERLAP", 200)})'
        )
        if preview and preview > 0:
            self.stdout.write(
                self.style.NOTICE(
                    f'Prévia abaixo: primeiros {preview} caracteres de cada chunk (não o fim do chunk). '
                    f'Usa --preview 0 para o texto completo.'
                )
            )
        self.stdout.write('')

        shown = chunks if limit is None else chunks[: max(0, limit)]
        for i, chunk in enumerate(shown):
            self.stdout.write(self.style.HTTP_INFO(f'--- chunk {i} — {len(chunk)} caracteres ---'))
            if preview == 0:
                self.stdout.write(chunk)
            else:
                snippet = chunk if len(chunk) <= preview else chunk[:preview] + '…'
                self.stdout.write(snippet)
            self.stdout.write('')

        if limit is not None and len(chunks) > len(shown):
            omit = len(chunks) - len(shown)
            self.stdout.write(
                self.style.WARNING(
                    f'… não mostrados {omit} chunk(s) devido a --limit={limit}. '
                    f'Para ver todos, corre sem --limit ou com --limit maior.'
                )
            )
