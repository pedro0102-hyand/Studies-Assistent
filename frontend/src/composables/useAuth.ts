import { ref } from 'vue'
import { API_BASE } from '@/config'
import { apiFetch } from '@/lib/api'

export interface MeUser {
  id: number
  username: string
  email: string
}

const user = ref<MeUser | null>(null)
/** true depois de tentar restaurar sessão ao arrancar */
const sessionReady = ref(false)

let sessionBoot: Promise<void> | null = null

function formatApiErrors(data: Record<string, unknown>): string {
  if (typeof data.detail === 'string') return data.detail
  const lines: string[] = []
  for (const [key, val] of Object.entries(data)) {
    if (key === 'detail') continue
    if (Array.isArray(val)) lines.push(`${key}: ${val.join(' ')}`)
    else if (typeof val === 'string') lines.push(`${key}: ${val}`)
  }
  return lines.length ? lines.join(' | ') : 'Pedido inválido'
}

export function useAuth() {
  async function fetchMe(): Promise<void> {
    const res = await apiFetch('/api/auth/me/')
    if (!res.ok) {
      user.value = null
      return
    }
    user.value = (await res.json()) as MeUser
  }

  /**
   * Restaura sessão via cookies; se access expirou, apiFetch renova com refresh.
   * Idempotente e seguro com navegações em paralelo (router).
   */
  async function initSession(): Promise<void> {
    if (sessionReady.value) return
    if (sessionBoot) {
      await sessionBoot
      return
    }
    sessionBoot = (async () => {
      try {
        await fetchMe()
      } finally {
        sessionReady.value = true
      }
    })()
    try {
      await sessionBoot
    } finally {
      sessionBoot = null
    }
  }

  async function login(username: string, password: string): Promise<{ ok: boolean; error?: string }> {
    const res = await fetch(`${API_BASE}/api/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, password }),
    })
    if (!res.ok) {
      const err = (await res.json().catch(() => ({}))) as { detail?: string }
      return { ok: false, error: err.detail ?? `Credenciais inválidas (${res.status})` }
    }
    await fetchMe()
    return { ok: true }
  }

  async function register(
    username: string,
    email: string,
    password: string,
    passwordConfirm: string,
  ): Promise<{ ok: boolean; error?: string }> {
    const res = await fetch(`${API_BASE}/api/auth/register/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        username,
        email: email.trim() || '',
        password,
        password_confirm: passwordConfirm,
      }),
    })
    if (!res.ok) {
      const data = (await res.json().catch(() => ({}))) as Record<string, unknown>
      return { ok: false, error: formatApiErrors(data) }
    }
    return login(username, password)
  }

  async function logout(): Promise<void> {
    await fetch(`${API_BASE}/api/auth/logout/`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
    user.value = null
  }

  return {
    user,
    sessionReady,
    initSession,
    fetchMe,
    login,
    register,
    logout,
  }
}
