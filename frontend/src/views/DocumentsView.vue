<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch } from '@/lib/api'
import { useAuth } from '@/composables/useAuth'
import ThemeToggle from '@/components/ThemeToggle.vue'

export interface ApiDocument {
  id: number
  original_name: string
  file_url: string
  text_char_count?: number
  chunk_count?: number
  embedded_chunk_count?: number
  embedding_error?: string
  chroma_indexed_at?: string | null
  chroma_error?: string
  extraction_error?: string
  created_at: string
  updated_at: string
}

const router = useRouter()
const { user, logout } = useAuth()

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
    if (!res.ok) throw new Error(`Erro ${res.status}`)
    documents.value = (await res.json()) as ApiDocument[]
  } catch (e) {
    listError.value = e instanceof Error ? e.message : 'Erro ao carregar'
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
      throw new Error(typeof data.detail === 'string' ? data.detail : `Erro ${res.status}`)
    }
    uploadMessage.value = `"${file.name}" enviado com sucesso.`
    await loadDocuments()
  } catch (e) {
    uploadError.value = e instanceof Error ? e.message : 'Falha no envio'
  } finally {
    uploadPending.value = false
  }
}

async function removeDoc(doc: ApiDocument) {
  if (!confirm(`Apagar "${doc.original_name}"?`)) return
  deletePending.value = doc.id
  uploadError.value = null
  try {
    const res = await apiFetch(`/api/documents/${doc.id}/`, { method: 'DELETE' })
    if (!res.ok && res.status !== 204) throw new Error(`Erro ${res.status}`)
    uploadMessage.value = 'Documento removido.'
    await loadDocuments()
  } catch (e) {
    uploadError.value = e instanceof Error ? e.message : 'Erro ao apagar'
  } finally {
    deletePending.value = null
  }
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
  } catch { return iso }
}

function statusInfo(doc: ApiDocument) {
  if (doc.extraction_error) return { type: 'error', text: 'Erro na extração' }
  if (doc.chroma_indexed_at) return { type: 'ok', text: 'Indexado' }
  if (doc.chroma_error) return { type: 'warn', text: 'Erro no índice' }
  if (doc.embedded_chunk_count) return { type: 'warn', text: 'Aguardando indexação' }
  return { type: 'idle', text: 'Processando...' }
}

async function onLogout() {
  await logout()
  router.push('/login')
}

onMounted(() => {
  loadDocuments()
})
</script>

<template>
  <div class="docs-layout">

    <!-- Sidebar -->
    <aside class="docs-sidebar">
      <div class="docs-sidebar-top">
        <button class="back-btn" @click="router.push('/chat')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          Chat
        </button>
        <button class="back-btn" @click="router.push('/materials')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            <path d="M8 7h9M8 11h9M8 15h7"/>
          </svg>
          Materiais
        </button>
        <div class="docs-theme">
          <ThemeToggle />
        </div>
      </div>

      <div class="docs-sidebar-bottom">
        <button class="sidebar-user" @click="onLogout">
          <div class="user-avatar">{{ user?.username?.[0]?.toUpperCase() ?? '?' }}</div>
          <span class="user-name">{{ user?.username }}</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>
          </svg>
        </button>
      </div>
    </aside>

    <!-- Conteúdo principal -->
    <main class="docs-main">
      <div class="docs-content">

        <header class="docs-header">
          <h1 class="docs-title">Meus PDFs</h1>
          <p class="docs-sub">Envie seus materiais em PDF para o assistente responder com base neles. Limite: 25 MB.</p>
        </header>

        <!-- Upload -->
        <div class="upload-area">
          <input
            ref="fileInput"
            type="file"
            accept=".pdf,application/pdf"
            class="sr-only"
            @change="onFileChange"
          />
          <button
            class="btn btn-secondary upload-btn"
            :disabled="uploadPending"
            @click="pickFile"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="16 16 12 12 8 16"/>
              <line x1="12" y1="12" x2="12" y2="21"/>
              <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>
            </svg>
            {{ uploadPending ? 'Enviando...' : 'Enviar PDF' }}
          </button>

          <div v-if="uploadMessage" class="feedback-ok">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            {{ uploadMessage }}
          </div>
          <div v-if="uploadError" class="feedback-err">{{ uploadError }}</div>
        </div>

        <!-- Lista -->
        <div class="docs-list-area">
          <div v-if="listLoading" class="list-loading">
            <div class="skel-row" /><div class="skel-row" /><div class="skel-row skel-row--sm" />
          </div>
          <div v-else-if="listError" class="feedback-err">{{ listError }}</div>
          <div v-else-if="documents.length === 0" class="list-empty">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            <p>Nenhum PDF ainda. Envie um arquivo para começar.</p>
          </div>
          <ul v-else class="doc-list">
            <li v-for="doc in documents" :key="doc.id" class="doc-item">
              <div class="doc-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
              </div>
              <div class="doc-info">
                <span class="doc-name" :title="doc.original_name">{{ doc.original_name }}</span>
                <div class="doc-meta">
                  <span
                    class="doc-status"
                    :class="`status-${statusInfo(doc).type}`"
                  >{{ statusInfo(doc).text }}</span>
                  <span class="doc-sep">·</span>
                  <span>{{ doc.chunk_count ?? 0 }} chunks</span>
                  <span class="doc-sep">·</span>
                  <span>{{ formatDate(doc.created_at) }}</span>
                </div>
              </div>
              <div class="doc-actions">
                <a
                  :href="doc.file_url"
                  target="_blank"
                  rel="noopener"
                  class="btn btn-ghost btn-icon"
                  title="Abrir arquivo"
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                    <polyline points="15 3 21 3 21 9"/>
                    <line x1="10" y1="14" x2="21" y2="3"/>
                  </svg>
                </a>
                <button
                  class="btn btn-ghost btn-icon"
                  :disabled="deletePending === doc.id"
                  title="Apagar"
                  @click="removeDoc(doc)"
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>
                  </svg>
                </button>
              </div>
            </li>
          </ul>
        </div>

      </div>
    </main>
  </div>
</template>

<style scoped>
.docs-layout {
  display: flex;
  height: 100vh;
  background: var(--bg);
}

/* Sidebar */
.docs-sidebar {
  width: 200px;
  flex-shrink: 0;
  background: var(--bg-2);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 0.75rem 0.5rem;
}

.docs-sidebar-top {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-2);
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}

.back-btn:hover {
  background: var(--bg-hover);
  color: var(--text);
}

.docs-sidebar-bottom {
  border-top: 1px solid var(--border);
  padding-top: 0.5rem;
}

.docs-theme {
  padding: 0.35rem 0.45rem 0.45rem;
}

.sidebar-user {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.55rem 0.75rem;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  cursor: pointer;
  width: 100%;
  transition: background 0.12s;
}

.sidebar-user:hover {
  background: var(--bg-hover);
}

.user-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  flex-shrink: 0;
}

.user-name {
  flex: 1;
  font-size: 0.875rem;
  color: var(--text-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Main */
.docs-main {
  flex: 1;
  overflow-y: auto;
  padding: 2rem 1.5rem;
}

.docs-content {
  max-width: 640px;
  margin: 0 auto;
}

.docs-header {
  margin-bottom: 1.75rem;
}

.docs-title {
  font-size: 1.45rem;
  font-weight: 650;
  color: var(--text);
  margin-bottom: 0.25rem;
}

.docs-sub {
  font-size: 0.9rem;
  color: var(--text-2);
}

/* Upload */
.upload-area {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 1.75rem;
}

.upload-btn {
  gap: 0.5rem;
}

.feedback-ok {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8125rem;
  color: var(--accent);
}

.feedback-err {
  font-size: 0.8125rem;
  color: var(--danger);
}

/* Lista */
.docs-list-area {
  display: flex;
  flex-direction: column;
}

.list-loading {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.skel-row {
  height: 58px;
  border-radius: var(--radius);
  background: var(--bg-2);
  animation: pulse 1.5s ease-in-out infinite;
}

.skel-row--sm {
  height: 58px;
  width: 70%;
}

@keyframes pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.list-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 3rem 1rem;
  text-align: center;
  color: var(--text-3);
  font-size: 0.9rem;
}

.doc-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.doc-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  transition: border-color 0.15s;
}

.doc-item:hover {
  border-color: var(--border-strong);
}

.doc-icon {
  color: var(--text-3);
  flex-shrink: 0;
}

.doc-info {
  flex: 1;
  min-width: 0;
}

.doc-name {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.doc-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.3rem;
  font-size: 0.75rem;
  color: var(--text-3);
  margin-top: 0.2rem;
}

.doc-sep {
  color: var(--border-strong);
}

.doc-status {
  font-weight: 500;
}

.status-ok { color: var(--accent); }
.status-warn { color: #f59e0b; }
.status-error { color: var(--danger); }
.status-idle { color: var(--text-3); }

.doc-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.doc-actions .btn-ghost {
  color: var(--text-3);
}

.doc-actions .btn-ghost:hover {
  color: var(--text);
  background: var(--bg-hover);
}

/* Responsivo */
@media (max-width: 600px) {
  .docs-sidebar {
    display: none;
  }

  .docs-main {
    padding: 1.1rem 0.9rem;
  }
}
</style>