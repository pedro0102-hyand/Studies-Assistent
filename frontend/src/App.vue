<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { API_BASE } from '@/config'
import { useAuth } from '@/composables/useAuth'

const { user, sessionReady, initSession, login, logout } = useAuth()

const healthStatus = ref<string | null>(null)
const healthError = ref<string | null>(null)
const healthLoading = ref(true)

const loginUser = ref('')
const loginPass = ref('')
const loginError = ref<string | null>(null)
const loginPending = ref(false)

onMounted(async () => {
  try {
    const res = await fetch(`${API_BASE}/api/health/`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = (await res.json()) as { status: string }
    healthStatus.value = data.status
  } catch (e) {
    healthError.value = e instanceof Error ? e.message : 'Erro desconhecido'
  } finally {
    healthLoading.value = false
  }
  await initSession()
})

async function onSubmitLogin() {
  loginError.value = null
  loginPending.value = true
  const r = await login(loginUser.value.trim(), loginPass.value)
  loginPending.value = false
  if (!r.ok) {
    loginError.value = r.error ?? 'Falha no login'
    return
  }
  loginPass.value = ''
}
</script>

<template>
  <main class="page">
    <h1>Studies Assistant</h1>

    <section class="card" aria-live="polite">
      <h2>Backend</h2>
      <p v-if="healthLoading">A contactar <code>/api/health/</code>…</p>
      <p v-else-if="healthError" class="err">{{ healthError }}</p>
      <p v-else>
        <code>/api/health/</code>: <strong>{{ healthStatus }}</strong>
      </p>
    </section>

    <section class="card">
      <h2>Sessão (2.5)</h2>
      <p v-if="!sessionReady">A restaurar sessão…</p>
      <template v-else-if="user">
        <p>
          Autenticado: <strong>{{ user.username }}</strong> (id {{ user.id }}) —
          <span class="muted">{{ user.email || 'sem email' }}</span>
        </p>
        <p><code>GET /api/auth/me/</code> sincronizado com o token em <code>localStorage</code>.</p>
        <button type="button" class="btn" @click="logout">Terminar sessão</button>
      </template>
      <form v-else @submit.prevent="onSubmitLogin">
        <p class="muted">Login para testar tokens e <code>/api/auth/me/</code>.</p>
        <label>
          Utilizador
          <input v-model="loginUser" type="text" autocomplete="username" required />
        </label>
        <label>
          Palavra-passe
          <input v-model="loginPass" type="password" autocomplete="current-password" required />
        </label>
        <p v-if="loginError" class="err">{{ loginError }}</p>
        <button type="submit" class="btn primary" :disabled="loginPending">
          {{ loginPending ? 'A entrar…' : 'Entrar' }}
        </button>
      </form>
    </section>
  </main>
</template>

<style scoped>
.page {
  max-width: 40rem;
  margin: 0 auto;
  padding: 2rem;
  font-family: system-ui, sans-serif;
}

h1 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

h2 {
  font-size: 1rem;
  margin: 0 0 0.75rem;
}

.card {
  margin-bottom: 1.25rem;
  padding: 1rem;
  border-radius: 8px;
  background: #f4f4f5;
}

form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.9rem;
}

input {
  padding: 0.5rem 0.6rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  font: inherit;
}

.err {
  color: #b91c1c;
}

.muted {
  color: #52525b;
  font-size: 0.9rem;
}

.btn {
  align-self: flex-start;
  padding: 0.45rem 0.9rem;
  border-radius: 6px;
  border: 1px solid #ccc;
  background: #fff;
  cursor: pointer;
  font: inherit;
}

.btn.primary {
  background: #18181b;
  color: #fff;
  border-color: #18181b;
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

code {
  font-size: 0.9em;
}
</style>
