<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { apiFetch } from '@/lib/api'

interface RagSource {
  document_id: number
  chunk_index: number
  original_name: string
  excerpt: string
}

const question = ref('')
const answer = ref<string | null>(null)
const sources = ref<RagSource[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const canSubmit = computed(
  () => question.value.trim().length > 0 && !loading.value,
)

async function submit() {
  error.value = null
  answer.value = null
  sources.value = []
  const q = question.value.trim()
  if (!q) return

  loading.value = true
  try {
    const res = await apiFetch('/api/rag/ask/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q }),
    })
    const data = (await res.json().catch(() => ({}))) as {
      detail?: string
      answer?: string
      sources?: RagSource[]
    }
    if (!res.ok) {
      throw new Error(
        typeof data.detail === 'string' ? data.detail : `Erro ${res.status}`,
      )
    }
    answer.value = data.answer ?? ''
    sources.value = Array.isArray(data.sources) ? data.sources : []
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Falha ao obter resposta'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const ta = document.querySelector('.ask__textarea') as HTMLTextAreaElement | null
  ta?.focus()
})
</script>

<template>
  <main class="sa-page ask">
    <RouterLink class="sa-page__back" to="/app">
      <span aria-hidden="true">←</span> Área da app
    </RouterLink>

    <header class="ask__header">
      <h1 class="ask__title">Perguntar aos PDFs</h1>
      <p class="ask__lead">
        A resposta usa apenas os documentos que indexaste (Chroma + Ollama). Garante que o
        Ollama está a correr e que os PDFs foram processados.
      </p>
    </header>

    <section class="sa-card sa-card--pad sa-card--elevated ask__form">
      <label class="ask__label" for="rag-question">A tua pergunta</label>
      <textarea
        id="rag-question"
        v-model="question"
        class="ask__textarea"
        rows="5"
        placeholder="Ex.: Resume o tema principal do manual."
        autocomplete="off"
      />
      <button
        type="button"
        class="sa-btn sa-btn--primary ask__btn"
        :disabled="!canSubmit"
        @click="submit"
      >
        {{ loading ? 'A pensar…' : 'Enviar' }}
      </button>
      <p v-if="error" class="ask__err" role="alert">{{ error }}</p>
    </section>

    <section v-if="answer !== null" class="ask__out sa-card sa-card--pad">
      <h2 class="ask__h2">Resposta</h2>
      <div class="ask__answer">{{ answer }}</div>

      <template v-if="sources.length">
        <h3 class="ask__h3">Fontes</h3>
        <ul class="ask__sources">
          <li v-for="(s, i) in sources" :key="`${s.document_id}-${s.chunk_index}-${i}`" class="ask__source">
            <span class="ask__source-meta">
              {{ s.original_name }} · chunk {{ s.chunk_index }}
            </span>
            <p class="ask__excerpt">{{ s.excerpt }}</p>
          </li>
        </ul>
      </template>
    </section>
  </main>
</template>

<style scoped>
.ask {
  padding-bottom: 3rem;
  max-width: 42rem;
}

.ask__header {
  margin-bottom: 1.5rem;
}

.ask__title {
  font-size: clamp(1.45rem, 3vw, 1.85rem);
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--sa-text);
  margin-bottom: 0.35rem;
}

.ask__lead {
  font-size: 0.95rem;
  color: var(--sa-text-muted);
  line-height: 1.55;
}

.ask__form {
  margin-bottom: 1.5rem;
}

.ask__label {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--sa-text);
}

.ask__textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 0.75rem 0.85rem;
  border-radius: var(--sa-radius-sm);
  border: 1px solid var(--sa-border);
  background: var(--sa-surface);
  color: var(--sa-text);
  font-size: 0.95rem;
  line-height: 1.5;
  resize: vertical;
  min-height: 7rem;
  margin-bottom: 1rem;
}

.ask__textarea:focus {
  outline: 2px solid var(--sa-primary-soft);
  border-color: var(--sa-primary);
}

.ask__btn {
  width: 100%;
}

.ask__err {
  margin-top: 0.85rem;
  font-size: 0.9rem;
  color: var(--sa-danger);
}

.ask__h2 {
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
  color: var(--sa-text);
}

.ask__h3 {
  font-size: 0.9rem;
  font-weight: 700;
  margin: 1.25rem 0 0.5rem;
  color: var(--sa-text-muted);
}

.ask__answer {
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--sa-text);
  white-space: pre-wrap;
}

.ask__sources {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.ask__source {
  padding: 0.65rem 0.75rem;
  border-radius: var(--sa-radius-sm);
  border: 1px solid var(--sa-border);
  background: color-mix(in srgb, var(--sa-surface) 92%, var(--sa-bg));
}

.ask__source-meta {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--sa-primary);
}

.ask__excerpt {
  margin: 0.35rem 0 0;
  font-size: 0.8rem;
  color: var(--sa-text-muted);
  line-height: 1.45;
}
</style>
