"""
Inspeciona o ChromaDB local (sem instalar UI à parte).

Exemplos:
  python manage.py chroma_inspect
  python manage.py chroma_inspect --document 5
  python manage.py chroma_inspect --limit 10
"""
from __future__ import annotations

import chromadb
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Mostra quantos pontos existem na coleção Chroma e uma amostra (ids, metadados, texto).'

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            '--document',
            '-d',
            type=int,
            default=None,
            metavar='ID',
            help='Filtrar apenas vetores deste document_id',
        )
        parser.add_argument(
            '--limit',
            '-n',
            type=int,
            default=8,
            metavar='N',
            help='Máximo de registos a mostrar (predefinição: 8)',
        )

    def handle(self, *args, **options) -> None:
        path = settings.CHROMA_PERSIST_PATH
        name = getattr(settings, 'CHROMA_COLLECTION_NAME', 'study_documents')
        doc_filter = options['document']
        lim = max(1, min(options['limit'], 500))

        self.stdout.write(f'Pasta Chroma: {path}')
        self.stdout.write(f'Coleção: {name}\n')

        try:
            client = chromadb.PersistentClient(path=str(path))
        except Exception as exc:
            raise CommandError(f'Não foi possível abrir o Chroma em {path}: {exc}') from exc

        try:
            coll = client.get_collection(name)
        except Exception as exc:
            raise CommandError(
                f'Coleção {name!r} ainda não existe (indexa um PDF primeiro). Erro: {exc}'
            ) from exc

        try:
            n_total = coll.count()
        except Exception as exc:
            raise CommandError(f'Falha ao contar: {exc}') from exc

        self.stdout.write(self.style.SUCCESS(f'Total de pontos na coleção: {n_total}\n'))

        where = None
        if doc_filter is not None:
            where = {'document_id': doc_filter}

        try:
            res = coll.get(
                where=where,
                limit=lim,
                include=['metadatas', 'documents'],
            )
        except Exception as exc:
            if doc_filter is None:
                raise CommandError(f'Falha ao ler registos: {exc}') from exc
            try:
                res = coll.get(
                    where={'document_id': {'$eq': doc_filter}},
                    limit=lim,
                    include=['metadatas', 'documents'],
                )
            except Exception as exc2:
                raise CommandError(f'Falha ao ler registos: {exc2}') from exc2

        ids = res.get('ids') or []
        metas = res.get('metadatas') or []
        docs = res.get('documents') or []

        if not ids:
            self.stdout.write(
                self.style.WARNING(
                    'Nenhum registo encontrado'
                    + (f' para document_id={doc_filter}' if doc_filter is not None else '')
                    + '.'
                )
            )
            return

        self.stdout.write(f'A mostrar até {len(ids)} registo(s):\n')
        for i, rid in enumerate(ids):
            meta = metas[i] if i < len(metas) else {}
            doc = docs[i] if i < len(docs) else ''
            preview = (doc[:120] + '…') if len(doc) > 120 else doc
            self.stdout.write(self.style.HTTP_INFO(f'  [{i}] id={rid!r}'))
            self.stdout.write(f'      meta={meta}')
            self.stdout.write(f'      texto: {preview!r}\n')
