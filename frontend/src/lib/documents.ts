import { apiFetch } from '@/lib/api'
import { fetchAllPaginatedResults } from '@/lib/paginatedList'
import type { ApiDocument } from '@/types/api'

export type DocumentStatusType = 'ok' | 'warn' | 'error' | 'idle'

export function getDocumentStatus(doc: ApiDocument): { type: DocumentStatusType; text: string } {
  const st = doc.extraction_status
  if (st === 'failed' || doc.extraction_error) {
    return { type: 'error', text: 'Erro na extração' }
  }
  if (st === 'pending' || st === 'processing') {
    return { type: 'idle', text: 'A processar no servidor…' }
  }
  if (doc.chroma_indexed_at) return { type: 'ok', text: 'Indexado' }
  if (doc.chroma_error) return { type: 'warn', text: 'Erro no índice' }
  if (doc.embedded_chunk_count) return { type: 'warn', text: 'Aguardando indexação' }
  return { type: 'idle', text: 'Em fila…' }
}

export async function fetchUserDocuments(): Promise<ApiDocument[]> {
  return fetchAllPaginatedResults<ApiDocument>('/api/documents/', 50)
}

export async function pollDocumentProcessing(
  id: number,
  onError?: (message: string) => void,
): Promise<ApiDocument | null> {
  const intervalMs = 1500
  for (let i = 0; i < 200; i++) {
    const res = await apiFetch(`/api/documents/${id}/`)
    if (!res.ok) return null
    const doc = (await res.json()) as ApiDocument
    if (doc.extraction_status === 'failed') {
      if (doc.extraction_error) onError?.(doc.extraction_error)
      return doc
    }
    if (doc.extraction_status === 'done') return doc
    await new Promise((r) => setTimeout(r, intervalMs))
  }
  return null
}
