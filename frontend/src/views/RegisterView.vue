<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const { register } = useAuth()
const router = useRouter()

const username = ref('')
const email = ref('')
const password = ref('')
const passwordConfirm = ref('')
const error = ref<string | null>(null)
const pending = ref(false)

async function onSubmit() {
  error.value = null
  pending.value = true
  const r = await register(
    username.value.trim(),
    email.value.trim(),
    password.value,
    passwordConfirm.value,
  )
  pending.value = false
  if (!r.ok) {
    error.value = r.error ?? 'Registo falhou'
    return
  }
  await router.replace('/app')
}
</script>

<template>
  <div class="auth auth--register">
    <aside class="auth__aside" aria-hidden="true">
      <div class="auth__aside-inner">
        <p class="auth__aside-tag">Novo por aqui?</p>
        <h2 class="auth__aside-title">Cria a tua conta em poucos segundos.</h2>
        <p class="auth__aside-text">
          Vais poder sincronizar sessão com JWT e aceder às rotas protegidas da aplicação.
        </p>
      </div>
    </aside>

    <main class="auth__main">
      <RouterLink class="sa-page__back" to="/">
        <span aria-hidden="true">←</span> Voltar ao início
      </RouterLink>

      <div class="auth__card sa-card sa-card--pad sa-card--elevated">
        <header class="auth__head">
          <h1 class="auth__h1">Criar conta</h1>
          <p class="auth__sub">Escolhe um utilizador e uma palavra-passe segura.</p>
        </header>

        <form class="auth__form" @submit.prevent="onSubmit">
          <div class="sa-field">
            <label class="sa-label" for="reg-user">Usuário</label>
            <input
              id="reg-user"
              v-model="username"
              class="sa-input"
              type="text"
              autocomplete="username"
              required
            />
          </div>
          <div class="sa-field">
            <label class="sa-label" for="reg-email">
              Email <span class="optional">(opcional)</span>
            </label>
            <input
              id="reg-email"
              v-model="email"
              class="sa-input"
              type="email"
              autocomplete="email"
              placeholder="nome@email.com"
            />
          </div>
          <div class="sa-field">
            <label class="sa-label" for="reg-pass">Senha</label>
            <input
              id="reg-pass"
              v-model="password"
              class="sa-input"
              type="password"
              autocomplete="new-password"
              required
            />
          </div>
          <div class="sa-field">
            <label class="sa-label" for="reg-pass2">Confirmar Senha </label>
            <input
              id="reg-pass2"
              v-model="passwordConfirm"
              class="sa-input"
              type="password"
              autocomplete="new-password"
              required
            />
          </div>

          <div v-if="error" class="sa-alert sa-alert--error" role="alert">
            {{ error }}
          </div>

          <button type="submit" class="sa-btn sa-btn--primary sa-btn--block" :disabled="pending">
            {{ pending ? 'A criar conta…' : 'Criar conta' }}
          </button>
        </form>

        <p class="auth__footer">
          Já tens conta?
          <RouterLink to="/login">Entrar</RouterLink>
        </p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.optional {
  font-weight: 500;
  color: var(--sa-text-subtle);
}

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

  .auth--register .auth__aside {
    order: 2;
    border-radius: var(--sa-radius) 0 0 var(--sa-radius);
    margin: clamp(1rem, 3vw, 2rem) clamp(1rem, 3vw, 2rem) clamp(1rem, 3vw, 2rem) 0;
  }

  .auth--register .auth__main {
    order: 1;
  }
}

.auth__aside {
  display: none;
  position: relative;
  padding: clamp(2rem, 5vw, 3rem);
  background: linear-gradient(215deg, #1e1b4b 0%, var(--sa-accent) 50%, #c026d3 100%);
  color: #fff;
}

@media (min-width: 900px) {
  .auth__aside {
    display: flex;
    align-items: center;
    justify-content: center;
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
  opacity: 0.9;
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
  max-width: calc(var(--sa-max-narrow) + 40px);
  width: 100%;
  margin: 0 auto;
}

.auth__card {
  width: 100%;
}

.auth__head {
  margin-bottom: 1.35rem;
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
  gap: 1rem;
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
