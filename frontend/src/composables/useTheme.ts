import { ref } from 'vue'

export type ThemeMode = 'dark' | 'light'

const STORAGE_KEY = 'studies_theme'
const theme = ref<ThemeMode>('dark')
let booted = false

function applyToDom(mode: ThemeMode) {
  const root = document.documentElement
  root.dataset.theme = mode
}

function readStored(): ThemeMode | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw === 'dark' || raw === 'light') return raw
    return null
  } catch {
    return null
  }
}

function writeStored(mode: ThemeMode) {
  try {
    localStorage.setItem(STORAGE_KEY, mode)
  } catch {}
}

export function useTheme() {
  function initTheme() {
    if (booted) return
    booted = true
    const stored = readStored()
    const mode: ThemeMode =
      stored ??
      (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches
        ? 'light'
        : 'dark')
    theme.value = mode
    applyToDom(mode)
  }

  function setTheme(mode: ThemeMode) {
    theme.value = mode
    applyToDom(mode)
    writeStored(mode)
  }

  function toggleTheme() {
    setTheme(theme.value === 'dark' ? 'light' : 'dark')
  }

  return { theme, initTheme, setTheme, toggleTheme }
}

