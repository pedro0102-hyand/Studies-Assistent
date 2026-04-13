/** Base da API Django (Vite: define `VITE_API_BASE_URL` em `.env` se precisares) */
export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
