<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { API_BASE } from '@/config'
import { useAuth } from '@/composables/useAuth'

const { user } = useAuth()

const healthStatus = ref<string | null>(null)
const healthError = ref<string | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await fetch(`${API_BASE}/api/health/`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = (await res.json()) as { status: string }
    healthStatus.value = data.status
  } catch (e) {
    healthError.value = e instanceof Error ? e.message : 'Erro desconhecido'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <main class="sa-page">
    <section class="hero">
      <p class="hero__eyebrow">Estudos com IA</p>
      <h1 class="hero__title">
        O teu assistente para <span class="hero__gradient">PDFs e conversas</span>
      </h1>
      <p class="hero__lead">
        Página pública — sem login obrigatório. Liga o backend e começa a explorar rotas de autenticação
        quando estiveres pronto.
      </p>
      <div class="hero__actions">
        <RouterLink v-if="!user" class="hero__btn hero__btn--primary" to="/register">
          Criar conta
        </RouterLink>
        <RouterLink v-if="!user" class="hero__btn hero__btn--secondary" to="/login">
          Já tenho conta
        </RouterLink>
        <RouterLink v-else class="hero__btn hero__btn--primary" to="/app">
          Ir para a área da app
        </RouterLink>
      </div>
    </section>

    <div class="grid">
      <article class="sa-card sa-card--pad sa-card--elevated status-card">
        <h2 class="status-card__h">Estado do backend</h2>
        <p class="status-card__path">
          <code>/api/health/</code>
        </p>

        <div v-if="loading" class="status-card__body status-card__body--loading">
          <span class="skeleton skeleton--line" />
          <span class="skeleton skeleton--line short" />
        </div>

        <div v-else-if="healthError" class="status-card__body">
          <div class="sa-status sa-status--err">
            <span class="sa-status__dot" />
            Offline ou erro
          </div>
          <p class="status-card__err">{{ healthError }}</p>
        </div>

        <div v-else class="status-card__body">
          <div class="sa-status sa-status--ok">
            <span class="sa-status__dot" />
            API disponível
          </div>
          <p class="status-card__ok">
            Resposta: <strong>{{ healthStatus }}</strong>
          </p>
        </div>
      </article>

      <article class="sa-card sa-card--pad hint-card">
        <h3 class="hint-card__h">Próximos passos</h3>
        <ul class="hint-card__list">
          <li>Regista-te ou entra para testar JWT e <code>/api/auth/me/</code>.</li>
          <li>A rota <strong>/app</strong> só é acessível autenticado.</li>
        </ul>
      </article>
    </div>
  </main>
</template>

<style scoped>
.hero {
  margin-bottom: clamp(1.75rem, 5vw, 2.75rem);
  max-width: 38rem;
}

.hero__eyebrow {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--sa-primary);
  margin-bottom: 0.75rem;
}

.hero__title {
  font-size: clamp(1.65rem, 4.5vw, 2.35rem);
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.03em;
  color: var(--sa-text);
  margin-bottom: 1rem;
}

.hero__gradient {
  background: linear-gradient(135deg, var(--sa-primary), var(--sa-accent));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hero__lead {
  font-size: 1rem;
  color: var(--sa-text-muted);
  line-height: 1.65;
  margin-bottom: 1.5rem;
}

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.hero__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.7rem 1.2rem;
  border-radius: var(--sa-radius-full);
  font-size: 0.9375rem;
  font-weight: 600;
  text-decoration: none;
  transition:
    transform 0.12s ease,
    box-shadow 0.15s ease,
    filter 0.15s ease;
}

.hero__btn:active {
  transform: scale(0.98);
}

.hero__btn--primary {
  color: #fff;
  background: linear-gradient(135deg, var(--sa-primary), var(--sa-accent));
  box-shadow: 0 4px 20px rgba(79, 70, 229, 0.35);
}

.hero__btn--primary:hover {
  filter: brightness(1.05);
}

.hero__btn--secondary {
  color: var(--sa-text);
  background: var(--sa-surface);
  border: 1px solid var(--sa-border);
  box-shadow: var(--sa-shadow);
}

.hero__btn--secondary:hover {
  border-color: var(--sa-border-strong);
}

.grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: 1fr;
}

@media (min-width: 768px) {
  .grid {
    grid-template-columns: 1.2fr 1fr;
    align-items: start;
  }
}

.status-card__h {
  font-size: 0.8125rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--sa-text-muted);
  margin-bottom: 0.35rem;
}

.status-card__path {
  margin-bottom: 1rem;
}

.status-card__path code {
  font-size: 0.8125rem;
}

.status-card__body {
  min-height: 3.5rem;
}

.status-card__body--loading {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.skeleton {
  display: block;
  height: 0.65rem;
  border-radius: var(--sa-radius-full);
  background: linear-gradient(
    90deg,
    var(--sa-border) 0%,
    color-mix(in srgb, var(--sa-surface) 60%, var(--sa-border)) 50%,
    var(--sa-border) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.2s ease-in-out infinite;
}

.skeleton.short {
  width: 55%;
}

@keyframes shimmer {
  0% {
    background-position: 100% 0;
  }
  100% {
    background-position: -100% 0;
  }
}

.status-card__ok {
  margin-top: 0.65rem;
  font-size: 0.9375rem;
  color: var(--sa-text-muted);
}

.status-card__ok strong {
  color: var(--sa-text);
}

.status-card__err {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: var(--sa-danger);
}

.hint-card__h {
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
  color: var(--sa-text);
}

.hint-card__list {
  margin: 0;
  padding-left: 1.15rem;
  color: var(--sa-text-muted);
  font-size: 0.9rem;
  line-height: 1.65;
}

.hint-card__list li {
  margin-bottom: 0.5rem;
}

.hint-card__list li:last-child {
  margin-bottom: 0;
}
</style>
