import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
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
      path: '/app',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/documents',
      name: 'documents',
      component: () => import('@/views/DocumentsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/ask',
      name: 'ask',
      component: () => import('@/views/AskView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('@/views/ChatView.vue'),
      meta: { requiresAuth: true },
    },
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
    next({ name: 'home' })
    return
  }

  next()
})

export default router
