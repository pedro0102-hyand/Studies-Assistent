import { API_BASE } from '@/config'
import {
  clearStoredTokens,
  getStoredAccess,
  getStoredRefresh,
  setStoredAccessOnly,
  setStoredTokens,
} from '@/lib/authStorage'

function joinUrl(path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE}${p}`
}

/**
 * Renova o access token com o refresh guardado. Devolve false se falhar (tokens limpos).
 */
export async function refreshAccessToken(): Promise<boolean> {
  const refresh = getStoredRefresh()
  if (!refresh) {
    clearStoredTokens()
    return false
  }
  const res = await fetch(joinUrl('/api/auth/token/refresh/'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })
  if (!res.ok) {
    clearStoredTokens()
    return false
  }
  const data = (await res.json()) as { access: string; refresh?: string }
  if (data.refresh) {
    setStoredTokens(data.access, data.refresh)
  } else {
    setStoredAccessOnly(data.access)
  }
  return true
}

/**
 * `fetch` à API com `Authorization: Bearer` quando há access token.
 * Em 401 com token, tenta refresh uma vez e repete o pedido.
 */
export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const url = joinUrl(path)
  const headers = new Headers(init.headers)
  const access = getStoredAccess()
  if (access && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${access}`)
  }
  let res = await fetch(url, { ...init, headers })
  if (res.status === 401 && access) {
    const ok = await refreshAccessToken()
    if (ok) {
      const h2 = new Headers(init.headers)
      h2.set('Authorization', `Bearer ${getStoredAccess()!}`)
      res = await fetch(url, { ...init, headers: h2 })
    }
  }
  return res
}
