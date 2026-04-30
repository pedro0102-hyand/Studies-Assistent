import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      // Redireciona raiz para /chat (autenticado) ou /login
      path: '/',
      redirect: () => {
        const { user } = useAuth()
        return user.value ? '/chat' : '/login'
      },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('@/views/ChatView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/documents',
      name: 'documents',
      component: () => import('@/views/DocumentsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/materials',
      name: 'materials',
      component: () => import('@/views/StudyMaterialsView.vue'),
      meta: { requiresAuth: true },
    },
    // Redireciona rotas antigas
    { path: '/app', redirect: '/chat' },
    { path: '/ask', redirect: '/chat' },
  ],
})

router.beforeEach(async (to, _from, next) => {
  const { initSession, sessionReady, user } = useAuth()

  if (!sessionReady.value) {
    await initSession()
  }

  if (to.meta.requiresAuth && !user.value) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  if (to.meta.guestOnly && user.value) {
    next({ name: 'chat' })
    return
  }

  next()
})

export default router
