const ACCESS_KEY = 'studies_access_token'
const REFRESH_KEY = 'studies_refresh_token'

export function getStoredAccess(): string | null {
  return localStorage.getItem(ACCESS_KEY)
}

export function getStoredRefresh(): string | null {
  return localStorage.getItem(REFRESH_KEY)
}

export function setStoredTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_KEY, access)
  localStorage.setItem(REFRESH_KEY, refresh)
}

export function setStoredAccessOnly(access: string): void {
  localStorage.setItem(ACCESS_KEY, access)
}

export function clearStoredTokens(): void {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}
