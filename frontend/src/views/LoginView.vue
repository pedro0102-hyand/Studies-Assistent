<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const { login } = useAuth()
const route = useRoute()
const router = useRouter()

const username = ref('')
const password = ref('')
const error = ref<string | null>(null)
const pending = ref(false)

async function onSubmit() {
  error.value = null
  pending.value = true
  const r = await login(username.value.trim(), password.value)
  pending.value = false
  if (!r.ok) {
    error.value = r.error ?? 'Falha no login'
    return
  }
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/app'
  await router.replace(redirect || '/app')
}
</script>

<template>
  <div class="auth">
    <aside class="auth__aside" aria-hidden="true">
      <div class="auth__aside-inner">
        <p class="auth__aside-tag">Bem-vindo de volta</p>
        <h2 class="auth__aside-title">Continua os teus estudos de onde paraste.</h2>
        <p class="auth__aside-text">
          Acesso seguro com JWT. As tuas credenciais são enviadas apenas ao servidor da API.
        </p>
      </div>
    </aside>

    <main class="auth__main">
      <RouterLink class="sa-page__back" to="/">
        <span aria-hidden="true">←</span> Voltar ao início
      </RouterLink>

      <div class="auth__card sa-card sa-card--pad sa-card--elevated">
        <header class="auth__head">
          <h1 class="auth__h1">Entrar</h1>
          <p class="auth__sub">Utiliza a tua conta para aceder à área autenticada.</p>
        </header>

        <form class="auth__form" @submit.prevent="onSubmit">
          <div class="sa-field">
            <label class="sa-label" for="login-user">Usuário</label>
            <input
              id="login-user"
              v-model="username"
              class="sa-input"
              type="text"
              autocomplete="username"
              required
            />
          </div>
          <div class="sa-field">
            <label class="sa-label" for="login-pass">Senha</label>
            <input
              id="login-pass"
              v-model="password"
              class="sa-input"
              type="password"
              autocomplete="current-password"
              required
            />
          </div>

          <div v-if="error" class="sa-alert sa-alert--error" role="alert">
            {{ error }}
          </div>

          <button type="submit" class="sa-btn sa-btn--primary sa-btn--block" :disabled="pending">
            {{ pending ? 'A entrar…' : 'Entrar' }}
          </button>
        </form>

        <p class="auth__footer">
          Ainda não tens conta?
          <RouterLink to="/register">Criar conta</RouterLink>
        </p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.auth {
  display: grid;
  min-height: calc(100vh - var(--sa-header-h));
  grid-template-columns: 1fr;
}

@media (min-width: 900px) {
  .auth {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1.05fr);
    max-width: var(--sa-max);
    margin: 0 auto;
  }
}

.auth__aside {
  display: none;
  position: relative;
  padding: clamp(2rem, 5vw, 3rem);
  background: linear-gradient(145deg, #312e81 0%, var(--sa-primary) 45%, var(--sa-accent) 100%);
  color: #fff;
}

@media (min-width: 900px) {
  .auth__aside {
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 0 var(--sa-radius) var(--sa-radius) 0;
    margin: clamp(1rem, 3vw, 2rem) 0 clamp(1rem, 3vw, 2rem) clamp(1rem, 3vw, 2rem);
    box-shadow: var(--sa-shadow-lg);
  }
}

.auth__aside-inner {
  max-width: 22rem;
}

.auth__aside-tag {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  opacity: 0.85;
  margin-bottom: 1rem;
}

.auth__aside-title {
  font-size: clamp(1.35rem, 2.5vw, 1.75rem);
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: -0.02em;
  margin-bottom: 0.75rem;
}

.auth__aside-text {
  font-size: 0.95rem;
  line-height: 1.65;
  opacity: 0.92;
}

.auth__main {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: clamp(1.25rem, 4vw, 2.5rem);
  max-width: var(--sa-max-narrow);
  width: 100%;
  margin: 0 auto;
}

.auth__card {
  width: 100%;
}

.auth__head {
  margin-bottom: 1.5rem;
}

.auth__h1 {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--sa-text);
  margin-bottom: 0.35rem;
}

.auth__sub {
  font-size: 0.9rem;
  color: var(--sa-text-muted);
  line-height: 1.5;
}

.auth__form {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.auth__footer {
  margin-top: 1.35rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--sa-border);
  font-size: 0.9rem;
  color: var(--sa-text-muted);
  text-align: center;
}

.auth__footer a {
  font-weight: 600;
}
</style>
