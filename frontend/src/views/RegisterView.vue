<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import ThemeToggle from '@/components/ThemeToggle.vue'

const { register } = useAuth()
const router = useRouter()

const username = ref('')
const email = ref('')
const password = ref('')
const passwordConfirm = ref('')
const showPassword = ref(false)
const showPasswordConfirm = ref(false)
const error = ref<string | null>(null)
const pending = ref(false)

async function onSubmit() {
  error.value = null
  if (!username.value.trim() || !password.value) {
    error.value = 'Preencha os campos obrigatórios.'
    return
  }
  if (password.value !== passwordConfirm.value) {
    error.value = 'As senhas não coincidem.'
    return
  }
  pending.value = true
  const r = await register(
    username.value.trim(),
    email.value.trim(),
    password.value,
    passwordConfirm.value,
  )
  pending.value = false
  if (!r.ok) {
    error.value = r.error ?? 'Erro ao criar conta'
    return
  }
  await router.replace('/chat')
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-top">
        <ThemeToggle />
      </div>

      <div class="auth-logo">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      </div>

      <h1 class="auth-title">Criar conta</h1>
      <p class="auth-sub">Crie sua conta e organize seus estudos com seus PDFs.</p>

      <form class="auth-form" @submit.prevent="onSubmit" novalidate>
        <div class="field">
          <label class="label" for="username">
            Usuário <span class="req">*</span>
          </label>
          <input
            id="username"
            v-model="username"
            class="input"
            type="text"
            autocomplete="username"
            placeholder="Escolha um usuário"
            autofocus
          />
        </div>

        <div class="field">
          <label class="label" for="email">
            Email <span class="opt">(opcional)</span>
          </label>
          <input
            id="email"
            v-model="email"
            class="input"
            type="email"
            autocomplete="email"
            placeholder="nome@exemplo.com"
          />
        </div>

        <div class="field">
          <label class="label" for="password">
            Senha <span class="req">*</span>
          </label>
          <div class="input-wrap">
            <input
              id="password"
              v-model="password"
              class="input input--has-icon"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="new-password"
              placeholder="••••••••"
            />
            <button type="button" class="eye-btn" :title="showPassword ? 'Ocultar' : 'Mostrar'" @click="showPassword = !showPassword">
              <svg v-if="!showPassword" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              <svg v-else width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="field">
          <label class="label" for="password-confirm">
            Confirmar senha <span class="req">*</span>
          </label>
          <div class="input-wrap">
            <input
              id="password-confirm"
              v-model="passwordConfirm"
              class="input input--has-icon"
              :type="showPasswordConfirm ? 'text' : 'password'"
              autocomplete="new-password"
              placeholder="••••••••"
            />
            <button type="button" class="eye-btn" :title="showPasswordConfirm ? 'Ocultar' : 'Mostrar'" @click="showPasswordConfirm = !showPasswordConfirm">
              <svg v-if="!showPasswordConfirm" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              <svg v-else width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
            </button>
          </div>
        </div>

        <div v-if="error" class="alert alert-error">{{ error }}</div>

        <button type="submit" class="submit-btn" :disabled="pending">
          {{ pending ? 'Criando...' : 'Criar conta' }}
        </button>
      </form>

      <p class="auth-footer">
        Já tem conta? <RouterLink to="/login">Entrar</RouterLink>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
  padding: 1.5rem;
}

.auth-card {
  width: 100%;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  align-items: center;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-2);
  box-shadow: var(--shadow);
  padding: 1.15rem 1.15rem 1.25rem;
}

.auth-top {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  margin-bottom: 0.75rem;
}

.auth-logo {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: var(--bg);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  margin-bottom: 1.25rem;
}

.auth-title {
  font-size: 1.45rem;
  font-weight: 650;
  color: var(--text);
  margin-bottom: 0.25rem;
}

.auth-sub {
  font-size: 0.9rem;
  color: var(--text-2);
  margin-bottom: 2rem;
}

.auth-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.req { color: var(--danger); font-weight: 400; }
.opt { color: var(--text-3); font-weight: 400; font-size: 0.75rem; }

/* ── Input com botão de visibilidade ── */
.input-wrap {
  position: relative;
}

.input--has-icon {
  padding-right: 2.6rem;
}

.eye-btn {
  position: absolute;
  right: 0.6rem;
  top: 50%;
  transform: translateY(-50%);
  border: none;
  background: transparent;
  color: var(--text-3);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.2rem;
  border-radius: 4px;
  transition: color 0.12s, background 0.12s;
}

.eye-btn:hover {
  color: var(--text-2);
  background: var(--bg-hover);
}

.submit-btn {
  width: 100%;
  padding: 0.65rem;
  font-size: 0.9375rem;
  font-weight: 500;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.15s, opacity 0.15s;
  margin-top: 0.25rem;
}

.submit-btn:hover:not(:disabled) { background: var(--accent-hover); }
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.auth-footer {
  margin-top: 1.5rem;
  font-size: 0.875rem;
  color: var(--text-2);
  text-align: center;
}

.auth-footer a { color: var(--accent); font-weight: 500; }
</style>