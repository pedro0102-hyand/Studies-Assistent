import { apiFetch } from '@/lib/api'

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

function withPageQuery(path: string, page: number, pageSize: number): string {
  const joiner = path.includes('?') ? '&' : '?'
  return `${path}${joiner}page=${page}&page_size=${pageSize}`
}

/** Percorre `?page=&page_size=` enquanto `next` existir (máx. 200 páginas). */
export async function fetchAllPaginatedResults<T>(
  path: string,
  pageSize = 100,
): Promise<T[]> {
  const items: T[] = []
  const maxPages = 200
  for (let page = 1; page <= maxPages; page += 1) {
    const res = await apiFetch(withPageQuery(path, page, pageSize))
    if (!res.ok) throw new Error(`Erro ${res.status}`)
    const data = (await res.json()) as Paginated<T>
    const batch = data.results
    if (!Array.isArray(batch) || batch.length === 0) break
    items.push(...batch)
    if (!data.next) break
  }
  return items
}
