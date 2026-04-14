<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const { user, logout } = useAuth()
const router = useRouter()

const initial = computed(() => {
  const n = user.value?.username?.trim()
  if (!n) return '?'
  return n.charAt(0).toUpperCase()
})

async function onLogout() {
  await logout()
  await router.replace({ name: 'home' })
}
</script>

<template>
  <main class="sa-page dash">
    <RouterLink class="sa-page__back" to="/">
      <span aria-hidden="true">←</span> Início
    </RouterLink>

    <header class="dash__header">
      <h1 class="dash__title">Área autenticada</h1>
      <p class="dash__lead">Dados obtidos de <code>GET /api/auth/me/</code> com JWT válido.</p>
    </header>

    <section v-if="user" class="profile sa-card sa-card--elevated">
      <div class="profile__top">
        <div class="profile__avatar" :aria-label="`Avatar ${user.username}`">
          {{ initial }}
        </div>
        <div class="profile__meta">
          <h2 class="profile__name">{{ user.username }}</h2>
          <p class="profile__id">ID utilizador · {{ user.id }}</p>
        </div>
      </div>

      <dl class="profile__dl">
        <div class="profile__row">
          <dt>Email</dt>
          <dd>{{ user.email || '—' }}</dd>
        </div>
        <div class="profile__row">
          <dt>Estado</dt>
          <dd>
            <span class="badge">Sessão ativa</span>
          </dd>
        </div>
      </dl>

      <p class="profile__hint">
        Esta vista corresponde à rota protegida <code>/app</code> (<code>requiresAuth</code> no router).
      </p>

      <div class="profile__actions">
        <RouterLink class="sa-btn sa-btn--secondary dash__docs-link" to="/documents">
          Gerir PDFs
        </RouterLink>
        <button type="button" class="sa-btn sa-btn--ghost" @click="onLogout">Terminar sessão</button>
      </div>
    </section>
  </main>
</template>

<style scoped>
.dash {
  padding-bottom: 3rem;
}

.dash__header {
  margin-bottom: 1.5rem;
}

.dash__title {
  font-size: clamp(1.45rem, 3vw, 1.85rem);
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--sa-text);
  margin-bottom: 0.35rem;
}

.dash__lead {
  font-size: 0.95rem;
  color: var(--sa-text-muted);
  max-width: 36rem;
  line-height: 1.55;
}

.profile {
  padding: clamp(1.35rem, 4vw, 2rem);
  max-width: 36rem;
}

.profile__top {
  display: flex;
  align-items: center;
  gap: 1.1rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1.35rem;
  border-bottom: 1px solid var(--sa-border);
}

.profile__avatar {
  flex-shrink: 0;
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.35rem;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--sa-primary), var(--sa-accent));
  box-shadow: 0 6px 20px rgba(79, 70, 229, 0.35);
}

.profile__name {
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--sa-text);
  margin-bottom: 0.15rem;
}

.profile__id {
  font-size: 0.8125rem;
  color: var(--sa-text-muted);
}

.profile__dl {
  margin: 0;
}

.profile__row {
  display: grid;
  grid-template-columns: minmax(5rem, 7rem) 1fr;
  gap: 0.75rem 1rem;
  padding: 0.65rem 0;
  border-bottom: 1px solid var(--sa-border);
  font-size: 0.9375rem;
}

.profile__row:last-of-type {
  border-bottom: none;
}

.profile__row dt {
  color: var(--sa-text-subtle);
  font-weight: 600;
}

.profile__row dd {
  margin: 0;
  color: var(--sa-text);
  word-break: break-word;
}

.badge {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: var(--sa-radius-full);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--sa-success);
  background: var(--sa-success-bg);
  border: 1px solid rgba(5, 150, 105, 0.25);
}

.profile__hint {
  margin-top: 1.25rem;
  font-size: 0.85rem;
  color: var(--sa-text-muted);
  line-height: 1.55;
}

.profile__actions {
  margin-top: 1.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--sa-border);
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
}

.dash__docs-link {
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 480px) {
  .profile__row {
    grid-template-columns: 1fr;
    gap: 0.25rem;
  }
}
</style>
