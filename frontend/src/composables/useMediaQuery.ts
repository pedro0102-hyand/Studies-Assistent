import { onBeforeUnmount, onMounted, ref } from 'vue'

export function useMediaQuery(query: string) {
  const matches = ref(false)
  let mql: MediaQueryList | null = null

  function sync() {
    if (typeof window === 'undefined') return
    matches.value = window.matchMedia(query).matches
  }

  onMounted(() => {
    sync()
    if (typeof window === 'undefined') return
    mql = window.matchMedia(query)
    mql.addEventListener('change', sync)
  })

  onBeforeUnmount(() => {
    mql?.removeEventListener('change', sync)
  })

  return matches
}
