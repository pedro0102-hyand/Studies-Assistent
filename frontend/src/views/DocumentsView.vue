<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { apiFetch } from '@/lib/api'

export interface ApiDocument {
  id: number
  original_name: string
  file_url: string
  text_char_count?: number
  chunk_count?: number
  embedded_chunk_count?: number
  embedding_error?: string
  extraction_error?: string
  created_at: string
  updated_at: string
}

const documents = ref<ApiDocument[]>([])
const listLoading = ref(true)
const listError = ref<string | null>(null)

const fileInput = ref<HTMLInputElement | null>(null)
const uploadPending = ref(false)
const uploadMessage = ref<string | null>(null)
const uploadError = ref<string | null>(null)

const deletePending = ref<number | null>(null)

async function loadDocuments() {
  listError.value = null
  listLoading.value = true
  try {
    const res = await apiFetch('/api/documents/')
    if (!res.ok) {
      const err = (await res.json().catch(() => ({}))) as { detail?: string }
      throw new Error(err.detail ?? `Erro ${res.status}`)
    }
    documents.value = (await res.json()) as ApiDocument[]
  } catch (e) {
    listError.value = e instanceof Error ? e.message : 'Falha ao carregar documentos'
    documents.value = []
  } finally {
    listLoading.value = false
  }
}

function pickFile() {
  uploadError.value = null
  uploadMessage.value = null
  fileInput.value?.click()
}

async function onFileChange(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return

  uploadPending.value = true
  uploadError.value = null
  uploadMessage.value = null

  const form = new FormData()
  form.append('file', file)

  try {
    const res = await apiFetch('/api/documents/upload/', {
      method: 'POST',
      body: form,
    })
    if (!res.ok) {
      const data = (await res.json().catch(() => ({}))) as Record<string, unknown>
      const detail = data.detail
      const msg =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? JSON.stringify(detail)
            : `Erro ${res.status}`
      throw new Error(msg)
    }
    uploadMessage.value = `“${file.name}” enviado com sucesso.`
    await loadDocuments()
  } catch (e) {
    uploadError.value = e instanceof Error ? e.message : 'Falha no envio'
  } finally {
    uploadPending.value = false
  }
}

async function removeDoc(doc: ApiDocument) {
  if (!confirm(`Apagar “${doc.original_name}”?`)) return
  deletePending.value = doc.id
  uploadError.value = null
  try {
    const res = await apiFetch(`/api/documents/${doc.id}/`, { method: 'DELETE' })
    if (!res.ok && res.status !== 204) {
      const err = (await res.json().catch(() => ({}))) as { detail?: string }
      throw new Error(err.detail ?? `Erro ${res.status}`)
    }
    await loadDocuments()
    uploadMessage.value = 'Documento removido.'
  } catch (e) {
    uploadError.value = e instanceof Error ? e.message : 'Falha ao apagar'
  } finally {
    deletePending.value = null
  }
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString('pt-PT', {
      dateStyle: 'short',
      timeStyle: 'short',
    })
  } catch {
    return iso
  }
}

onMounted(() => {
  loadDocuments()
})
</script>

<template>
  <main class="sa-page docs">
    <RouterLink class="sa-page__back" to="/app">
      <span aria-hidden="true">←</span> Área da app
    </RouterLink>

    <header class="docs__header">
      <h1 class="docs__title">Os teus PDFs</h1>
      <p class="docs__lead">
        Envia ficheiros para o servidor, consulta a lista e apaga quando já não precisares.
      </p>
    </header>

    <section class="sa-card sa-card--pad sa-card--elevated docs__upload">
      <h2 class="docs__h2">Enviar PDF</h2>
      <p class="docs__hint">Máx. 25 MB · apenas <code>.pdf</code></p>
      <input
        ref="fileInput"
        type="file"
        accept=".pdf,application/pdf"
        class="docs__hidden-input"
        @change="onFileChange"
      />
      <button
        type="button"
        class="sa-btn sa-btn--primary"
        :disabled="uploadPending"
        @click="pickFile"
      >
        {{ uploadPending ? 'A enviar…' : 'Escolher ficheiro' }}
      </button>
      <p v-if="uploadMessage" class="docs__ok" role="status">{{ uploadMessage }}</p>
      <p v-if="uploadError" class="docs__err" role="alert">{{ uploadError }}</p>
    </section>

    <section class="docs__list-wrap">
      <h2 class="docs__h2">Documentos</h2>

      <p v-if="listLoading" class="docs__muted">A carregar…</p>
      <p v-else-if="listError" class="docs__err">{{ listError }}</p>
      <p v-else-if="documents.length === 0" class="docs__muted">Ainda não tens PDFs enviados.</p>

      <ul v-else class="docs__list" aria-label="Lista de PDFs">
        <li v-for="doc in documents" :key="doc.id" class="docs__item sa-card sa-card--pad">
          <div class="docs__item-main">
            <span class="docs__name" :title="doc.original_name">{{ doc.original_name }}</span>
            <span class="docs__date">{{ formatDate(doc.created_at) }}</span>
            <span
              v-if="doc.extraction_error"
              class="docs__meta docs__meta--err"
              :title="doc.extraction_error"
            >
              {{ doc.extraction_error }}
            </span>
            <template v-else>
              <span class="docs__meta">
                {{ doc.text_char_count ?? 0 }} caracteres · {{ doc.chunk_count ?? 0 }} chunks
                <template v-if="(doc.chunk_count ?? 0) > 0">
                  · {{ doc.embedded_chunk_count ?? 0 }} embeddings
                </template>
              </span>
              <span
                v-if="doc.embedding_error"
                class="docs__meta docs__meta--warn"
                :title="doc.embedding_error"
              >
                Embeddings: {{ doc.embedding_error }}
              </span>
            </template>
          </div>
          <div class="docs__item-actions">
            <a
              :href="doc.file_url"
              class="docs__link"
              target="_blank"
              rel="noopener noreferrer"
            >
              Abrir
            </a>
            <button
              type="button"
              class="sa-btn sa-btn--ghost docs__del"
              :disabled="deletePending === doc.id"
              @click="removeDoc(doc)"
            >
              {{ deletePending === doc.id ? '…' : 'Apagar' }}
            </button>
          </div>
        </li>
      </ul>
    </section>
  </main>
</template>

<style scoped>
.docs {
  padding-bottom: 3rem;
  max-width: 42rem;
}

.docs__header {
  margin-bottom: 1.5rem;
}

.docs__title {
  font-size: clamp(1.45rem, 3vw, 1.85rem);
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--sa-text);
  margin-bottom: 0.35rem;
}

.docs__lead {
  font-size: 0.95rem;
  color: var(--sa-text-muted);
  line-height: 1.55;
}

.docs__h2 {
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 0.35rem;
  color: var(--sa-text);
}

.docs__hint {
  font-size: 0.85rem;
  color: var(--sa-text-muted);
  margin-bottom: 1rem;
}

.docs__upload {
  margin-bottom: 2rem;
}

.docs__hidden-input {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

.docs__ok {
  margin-top: 0.85rem;
  font-size: 0.9rem;
  color: var(--sa-success);
}

.docs__err {
  margin-top: 0.85rem;
  font-size: 0.9rem;
  color: var(--sa-danger);
}

.docs__muted {
  font-size: 0.95rem;
  color: var(--sa-text-muted);
}

.docs__list {
  list-style: none;
  padding: 0;
  margin: 1rem 0 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.docs__item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.docs__item-main {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
  flex: 1;
}

.docs__name {
  font-weight: 600;
  color: var(--sa-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.docs__date {
  font-size: 0.8rem;
  color: var(--sa-text-muted);
}

.docs__meta {
  font-size: 0.75rem;
  color: var(--sa-text-muted);
  line-height: 1.35;
}

.docs__meta--err {
  color: var(--sa-danger);
}

.docs__meta--warn {
  color: var(--sa-warning, #b45309);
}

.docs__item-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.docs__link {
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.4rem 0.75rem;
  border-radius: var(--sa-radius-sm);
  border: 1px solid var(--sa-border);
  color: var(--sa-primary);
  text-decoration: none;
}

.docs__link:hover {
  background: var(--sa-primary-soft);
}

.docs__del {
  font-size: 0.875rem;
  padding: 0.4rem 0.65rem;
}

@media (max-width: 520px) {
  .docs__item {
    flex-direction: column;
    align-items: stretch;
  }

  .docs__item-actions {
    justify-content: flex-end;
  }
}
</style>
