import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

export function useLogout() {
  const router = useRouter()
  const { logout } = useAuth()

  async function onLogout() {
    await logout()
    await router.push('/login')
  }

  return { onLogout }
}
