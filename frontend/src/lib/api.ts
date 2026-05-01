import { API_BASE } from '@/config'

function joinUrl(path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE}${p}`
}

const defaultCredentials: RequestCredentials = 'include'

/**
 * Renova o access token (refresh em cookie HttpOnly ou no body).
 * Devolve false se falhar.
 */
export async function refreshAccessToken(): Promise<boolean> {
  const res = await fetch(joinUrl('/api/auth/token/refresh/'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: defaultCredentials,
    body: JSON.stringify({}),
  })
  if (!res.ok) {
    return false
  }
  return true
}

/**
 * `fetch` à API com cookies de sessão (JWT HttpOnly).
 * Em 401, tenta refresh uma vez e repete o pedido.
 */
export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const url = joinUrl(path)
  const headers = new Headers(init.headers)
  if (init.body instanceof FormData) {
    headers.delete('Content-Type')
  }
  const credentials = init.credentials ?? defaultCredentials
  let res = await fetch(url, { ...init, headers, credentials })
  if (res.status === 401) {
    const ok = await refreshAccessToken()
    if (ok) {
      const h2 = new Headers(init.headers)
      if (init.body instanceof FormData) {
        h2.delete('Content-Type')
      }
      res = await fetch(url, { ...init, headers: h2, credentials })
    }
  }
  return res
}
