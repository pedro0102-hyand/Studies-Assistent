"""
Gera embeddings (Ollama /api/embed) para os chunks de um Document e mostra estatísticas no terminal.

Exemplos:
  python manage.py show_embeddings --list
  python manage.py show_embeddings 5
  python manage.py show_embeddings 5 --limit 3
"""
from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from documents.chunking import split_into_chunks
from documents.models import Document
from documents.ollama_embed import OllamaEmbedError, embed_texts, vector_summary


class Command(BaseCommand):
    help = 'Chama o Ollama para gerar embeddings dos chunks de um documento e mostra dimensão e amostra.'

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            'document_id',
            nargs='?',
            type=int,
            default=None,
            help='ID do Document',
        )
        parser.add_argument(
            '--list',
            '-l',
            action='store_true',
            help='Listar documentos com ids',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            metavar='M',
            help='Gerar no máximo M chunks (para teste rápido; omite para todos)',
        )
        parser.add_argument(
            '--sample',
            type=int,
            default=8,
            metavar='K',
            help='Quantos valores iniciais do vetor mostrar por chunk (predefinição: 8)',
        )

    def _print_document_table(self) -> None:
        total = Document.objects.count()
        if total == 0:
            self.stdout.write(
                self.style.WARNING(
                    'Não há documentos. Envia um PDF pela app ou cria no admin.'
                )
            )
            return
        self.stdout.write(f'Documentos: {total} (até 50, mais recentes primeiro)\n')
        for d in Document.objects.order_by('-id')[:50]:
            self.stdout.write(
                f'  id={d.pk!s:<5} user_id={d.user_id!s:<4} chars={len(d.extracted_text or "")!s:<7} '
                f'chunks={d.chunk_count!s:<4} emb={d.embedded_chunk_count!s:<4} {d.original_name!r}'
            )

    def handle(self, *args, **options) -> None:
        if options['list']:
            self._print_document_table()
            return

        doc_id = options['document_id']
        if doc_id is None:
            raise CommandError(
                'Indica o id (ex.: show_embeddings 5) ou usa --list para ver ids.'
            )

        limit = options['limit']
        sample_k = max(0, options['sample'])

        try:
            doc = Document.objects.get(pk=doc_id)
        except Document.DoesNotExist:
            self._print_document_table()
            self.stdout.flush()
            raise CommandError(f'Document id={doc_id} não existe.')

        text = doc.extracted_text or ''
        if not text.strip():
            self.stdout.write(self.style.WARNING('Sem texto extraído.'))
            return

        chunks = split_into_chunks(
            text,
            chunk_size=getattr(settings, 'RAG_CHUNK_SIZE', 1500),
            overlap=getattr(settings, 'RAG_CHUNK_OVERLAP', 200),
        )
        if limit is not None:
            chunks = chunks[: max(0, limit)]

        base = getattr(settings, 'OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
        model = getattr(settings, 'OLLAMA_EMBED_MODEL', 'nomic-embed-text:latest')
        timeout = float(getattr(settings, 'OLLAMA_EMBED_TIMEOUT', 120))
        batch_size = int(getattr(settings, 'OLLAMA_EMBED_BATCH_SIZE', 32))

        self.stdout.write(
            f'Document #{doc.pk} — {doc.original_name!r}\n'
            f'Ollama: {base} · modelo: {model}\n'
            f'Chunks a embedar: {len(chunks)} (de {doc.original_name})\n'
        )

        try:
            vectors = embed_texts(
                chunks,
                base_url=base,
                model=model,
                timeout=timeout,
                batch_size=batch_size,
            )
        except OllamaEmbedError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            raise CommandError('Falha ao obter embeddings. Confirma que o Ollama está a correr e o modelo existe.') from exc

        if len(vectors) != len(chunks):
            raise CommandError(
                f'Contagem inesperada: {len(vectors)} vetores para {len(chunks)} chunks.'
            )

        dim = len(vectors[0]) if vectors else 0
        self.stdout.write(self.style.SUCCESS(f'OK — {len(vectors)} vetores × dimensão {dim}\n'))

        for i, (ch, vec) in enumerate(zip(chunks, vectors)):
            st = vector_summary(vec)
            head = vec[:sample_k] if sample_k else []
            head_str = ', '.join(f'{x:.6f}' for x in head)
            preview = (ch[:80] + '…') if len(ch) > 80 else ch
            self.stdout.write(self.style.HTTP_INFO(f'--- [{i}] len_text={len(ch)} ---'))
            self.stdout.write(f'  texto: {preview!r}')
            self.stdout.write(
                f'  vetor: dim={st["dim"]} min={st["min"]:.6f} max={st["max"]:.6f} '
                f'média={st["mean"]:.6f} ‖v‖₂={st["l2"]:.6f}'
            )
            if sample_k:
                self.stdout.write(f'  primeiros {sample_k} valores: [{head_str}]')
            self.stdout.write('')
