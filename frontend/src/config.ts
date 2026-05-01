/**
 * Base da API Django.
 * Em desenvolvimento, por defeito usa URL relativa + proxy do Vite (`/api` → backend)
 * para os cookies HttpOnly funcionarem (mesma origem que a página).
 * Para apontar direto ao backend (ex.: testes), define `VITE_API_BASE_URL` no `.env`.
 */
const envUrl = import.meta.env.VITE_API_BASE_URL
export const API_BASE =
  typeof envUrl === 'string' && envUrl.trim() !== ''
    ? envUrl.trim().replace(/\/$/, '')
    : import.meta.env.DEV
      ? ''
      : 'http://127.0.0.1:8000'
