export function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return iso
  }
}

export function apiErrorDetail(data: unknown, fallback: string): string {
  if (data && typeof data === 'object' && 'detail' in data) {
    const detail = (data as { detail?: unknown }).detail
    if (typeof detail === 'string') return detail
  }
  return fallback
}

export async function readApiError(res: Response): Promise<string> {
  const data = await res.json().catch(() => ({}))
  return apiErrorDetail(data, `Erro ${res.status}`)
}

export function userInitial(username?: string | null): string {
  return username?.[0]?.toUpperCase() ?? '?'
}
