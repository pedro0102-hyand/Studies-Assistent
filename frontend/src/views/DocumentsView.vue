<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiFetch } from '@/lib/api'
import { readApiError } from '@/lib/format'
import {
  fetchUserDocuments,
  getDocumentStatus,
  pollDocumentProcessing,
} from '@/lib/documents'
import { formatDate } from '@/lib/format'
import type { ApiDocument } from '@/types/api'
import AppSecondarySidebar from '@/components/AppSecondarySidebar.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const sidebarLinks = [
  { to: '/chat', label: 'Chat' },
  { to: '/materials', label: 'Materiais' },
]

const documents = ref<ApiDocument[]>([])
const listLoading = ref(true)
const listError = ref<string | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const uploadPending = ref(false)
const uploadMessage = ref<string | null>(null)
const uploadError = ref<string | null>(null)
const deletePending = ref<number | null>(null)
const deleteConfirmOpen = ref(false)
const deleteTarget = ref<ApiDocument | null>(null)

async function loadDocuments() {
  listError.value = null
  listLoading.value = true
  try {
    documents.value = await fetchUserDocuments()
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
    if (!res.ok) throw new Error(await readApiError(res))
    const created = (await res.json()) as ApiDocument
    uploadMessage.value = `"${file.name}" recebido. A processar no servidor…`
    await pollDocumentProcessing(created.id, (msg) => {
      uploadError.value = msg
    })
    uploadMessage.value = uploadError.value
      ? `"${file.name}" — falhou a extração.`
      : `"${file.name}" — processamento concluído (ver estado abaixo).`
    await loadDocuments()
  } catch (e) {
    uploadError.value = e instanceof Error ? e.message : 'Falha no envio'
  } finally {
    uploadPending.value = false
  }
}

function removeDoc(doc: ApiDocument) {
  deleteTarget.value = doc
  deleteConfirmOpen.value = true
}

async function confirmDeleteDoc() {
  const doc = deleteTarget.value
  deleteConfirmOpen.value = false
  deleteTarget.value = null
  if (!doc) return
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

onMounted(loadDocuments)
</script>

<template>
  <div class="docs-layout">
    <ConfirmDialog
      v-model:open="deleteConfirmOpen"
      title="Apagar PDF?"
      :description="deleteTarget ? `Isto remove o ficheiro e o índice do documento “${deleteTarget.original_name}”. Não é possível desfazer.` : 'Isto remove o ficheiro e o índice do documento. Não é possível desfazer.'"
      confirmText="Apagar"
      cancelText="Cancelar"
      variant="danger"
      @confirm="confirmDeleteDoc"
    />

    <AppSecondarySidebar :links="sidebarLinks" />

    <main class="docs-main">
      <div class="docs-content">
        <header class="docs-header">
          <h1 class="docs-title">Meus PDFs</h1>
          <p class="docs-sub">Envie seus materiais em PDF para o assistente responder com base neles. Limite: 25 MB.</p>
        </header>

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
            {{ uploadPending ? 'A enviar / processar…' : 'Enviar PDF' }}
          </button>
          <p v-if="uploadPending" class="upload-progress-hint">
            O ficheiro foi aceite; a extração e a indexação correm em segundo plano (podes aguardar ou voltar mais tarde).
          </p>
          <div v-if="uploadMessage" class="feedback-ok">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            {{ uploadMessage }}
          </div>
          <div v-if="uploadError" class="feedback-err">{{ uploadError }}</div>
        </div>

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
                  <span class="doc-status" :class="`status-${getDocumentStatus(doc).type}`">
                    {{ getDocumentStatus(doc).text }}
                  </span>
                  <span class="doc-sep">·</span>
                  <span>{{ doc.chunk_count ?? 0 }} chunks</span>
                  <span class="doc-sep">·</span>
                  <span>{{ formatDate(doc.created_at ?? '') }}</span>
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

.upload-progress-hint {
  font-size: 0.8rem;
  color: var(--text-3);
  margin: 0.35rem 0 0;
  max-width: 36rem;
  line-height: 1.45;
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

@media (max-width: 600px) {
  .docs-main {
    padding: 1.1rem 0.9rem;
  }
}
</style>
