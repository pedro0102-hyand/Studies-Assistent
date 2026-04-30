<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch } from '@/lib/api'
import { useAuth } from '@/composables/useAuth'
import { renderMarkdownToSafeHtml } from '@/lib/markdown'
import html2pdf from 'html2pdf.js'

type MaterialKind = 'summary' | 'exercise_list' | 'roadmap'

interface ApiDocument {
  id: number
  original_name: string
  chunk_count?: number
  chroma_indexed_at?: string | null
  chroma_error?: string
  extraction_error?: string
}

interface GenerateResponse {
  kind: MaterialKind
  title: string
  markdown: string
  sources?: Array<{
    document_id: number
    chunk_index: number
    original_name: string
    excerpt: string
  }>
}

const router = useRouter()
const { user, logout } = useAuth()

const docs = ref<ApiDocument[]>([])
const docsLoading = ref(true)
const docsError = ref<string | null>(null)

const kind = ref<MaterialKind>('summary')
const title = ref('')
const topic = ref('')
const instructions = ref('')
const onlyIndexed = ref(true)
const selectedDocIds = ref<number[]>([])

const generatePending = ref(false)
const generateError = ref<string | null>(null)
const result = ref<GenerateResponse | null>(null)

const previewHtml = computed(() => renderMarkdownToSafeHtml(result.value?.markdown ?? ''))
const canExportPdf = computed(() => !!result.value?.markdown && !generatePending.value)

const visibleDocs = computed(() => {
  const base = docs.value
  if (!onlyIndexed.value) return base
  return base.filter((d) => !!d.chroma_indexed_at && !d.extraction_error && !d.chroma_error)
})

function toggleDoc(id: number) {
  const s = new Set(selectedDocIds.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  selectedDocIds.value = [...s]
}

function selectAllVisible() {
  selectedDocIds.value = visibleDocs.value.map((d) => d.id)
}

function clearSelection() {
  selectedDocIds.value = []
}

function kindLabel(k: MaterialKind) {
  if (k === 'summary') return 'Resumo'
  if (k === 'exercise_list') return 'Lista de exercícios'
  return 'Roadmap'
}

async function loadDocs() {
  docsLoading.value = true
  docsError.value = null
  try {
    const res = await apiFetch('/api/documents/')
    if (!res.ok) throw new Error(`Erro ${res.status}`)
    docs.value = (await res.json()) as ApiDocument[]
  } catch (e) {
    docs.value = []
    docsError.value = e instanceof Error ? e.message : 'Erro ao carregar'
  } finally {
    docsLoading.value = false
  }
}

async function generate() {
  if (generatePending.value) return
  generatePending.value = true
  generateError.value = null
  result.value = null
  try {
    const payload = {
      kind: kind.value,
      title: title.value.trim() || undefined,
      topic: topic.value.trim() || undefined,
      instructions: instructions.value.trim() || undefined,
      document_ids: selectedDocIds.value.length ? selectedDocIds.value : undefined,
    }
    const res = await apiFetch('/api/rag/generate/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const data = (await res.json().catch(() => ({}))) as any
    if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `Erro ${res.status}`)
    result.value = data as GenerateResponse
  } catch (e) {
    generateError.value = e instanceof Error ? e.message : 'Falha ao gerar'
  } finally {
    generatePending.value = false
  }
}

async function exportPdf() {
  if (!result.value) return
  const el = document.getElementById('pdf-root')
  if (!el) return

  const safeTitle = (result.value.title || kindLabel(result.value.kind))
    .replace(/[\\/:*?"<>|]+/g, '-')
    .slice(0, 80)

  await html2pdf()
    .set({
      margin: [12, 12, 14, 12],
      filename: `${safeTitle}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2, useCORS: true, backgroundColor: '#ffffff' },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
      pagebreak: { mode: ['css', 'legacy'] },
    })
    .from(el)
    .save()
}

async function onLogout() {
  await logout()
  router.push('/login')
}

onMounted(() => {
  loadDocs()
})
</script>

<template>
  <div class="mat-layout">
    <!-- Sidebar -->
    <aside class="mat-sidebar">
      <div class="mat-sidebar-top">
        <button class="back-btn" @click="router.push('/chat')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          Chat
        </button>
        <button class="back-btn" @click="router.push('/documents')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          Meus PDFs
        </button>
      </div>

      <div class="mat-sidebar-bottom">
        <button class="sidebar-user" @click="onLogout">
          <div class="user-avatar">{{ user?.username?.[0]?.toUpperCase() ?? '?' }}</div>
          <span class="user-name">{{ user?.username }}</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>
          </svg>
        </button>
      </div>
    </aside>

    <!-- Conteúdo -->
    <main class="mat-main">
      <div class="mat-content">
        <header class="mat-header">
          <div class="mat-title-row">
            <div>
              <h1 class="mat-title">Materiais</h1>
              <p class="mat-sub">Gere resumos, listas de exercícios e roadmaps usando o conteúdo dos seus PDFs (RAG).</p>
            </div>
            <div class="mat-actions">
              <button class="btn btn-secondary" :disabled="generatePending" @click="generate">
                {{ generatePending ? 'Gerando...' : 'Gerar' }}
              </button>
              <button class="btn btn-ghost" :disabled="!canExportPdf" @click="exportPdf">
                Baixar PDF
              </button>
            </div>
          </div>
        </header>

        <div class="mat-grid">
          <!-- Config -->
          <section class="card">
            <h2 class="card-title">Configuração</h2>

            <div class="field">
              <label>Tipo</label>
              <div class="segmented">
                <button class="seg-btn" :class="{ active: kind === 'summary' }" @click="kind = 'summary'">Resumo</button>
                <button class="seg-btn" :class="{ active: kind === 'exercise_list' }" @click="kind = 'exercise_list'">Exercícios</button>
                <button class="seg-btn" :class="{ active: kind === 'roadmap' }" @click="kind = 'roadmap'">Roadmap</button>
              </div>
            </div>

            <div class="field">
              <label>Título (opcional)</label>
              <input v-model="title" class="input" placeholder="Ex.: Revisão para prova 1" />
            </div>

            <div class="field">
              <label>Tema / foco (opcional)</label>
              <input v-model="topic" class="input" placeholder="Ex.: Derivadas e aplicações" />
            </div>

            <div class="field">
              <label>Instruções extras (opcional)</label>
              <textarea v-model="instructions" class="textarea" rows="4" placeholder="Ex.: dê mais exemplos e uma checklist curta." />
            </div>

            <div v-if="generateError" class="feedback-err">{{ generateError }}</div>
          </section>

          <!-- Fontes -->
          <section class="card">
            <div class="card-title-row">
              <h2 class="card-title">Documentos</h2>
              <div class="mini-actions">
                <button class="link" type="button" @click="selectAllVisible">Selecionar</button>
                <span class="dot">·</span>
                <button class="link" type="button" @click="clearSelection">Limpar</button>
              </div>
            </div>

            <label class="checkline">
              <input v-model="onlyIndexed" type="checkbox" />
              <span>Mostrar apenas PDFs indexados</span>
            </label>

            <div v-if="docsLoading" class="skeleton">
              <div class="skel-row" /><div class="skel-row" /><div class="skel-row skel-row--sm" />
            </div>
            <div v-else-if="docsError" class="feedback-err">{{ docsError }}</div>
            <div v-else-if="visibleDocs.length === 0" class="empty">
              Nenhum PDF {{ onlyIndexed ? 'indexado' : '' }} encontrado.
            </div>
            <ul v-else class="doc-pick">
              <li v-for="d in visibleDocs" :key="d.id" class="doc-pick-item" @click="toggleDoc(d.id)">
                <input
                  class="doc-check"
                  type="checkbox"
                  :checked="selectedDocIds.includes(d.id)"
                  @change.prevent
                />
                <div class="doc-name" :title="d.original_name">{{ d.original_name }}</div>
              </li>
            </ul>

            <p class="hint">
              Se não selecionar nada, o sistema usa todos os seus documentos (com filtro por utilizador).
            </p>
          </section>

          <!-- Preview -->
          <section class="card preview-card">
            <div class="card-title-row">
              <h2 class="card-title">Preview</h2>
              <span v-if="result" class="badge">{{ kindLabel(result.kind) }}</span>
            </div>

            <div v-if="!result" class="empty preview-empty">
              Gere um material para ver o preview aqui.
            </div>

            <div v-else class="preview">
              <div class="preview-top">
                <h3 class="preview-title">{{ result.title }}</h3>
                <p class="preview-meta">
                  Baseado em {{ result.sources?.length ?? 0 }} trecho{{ (result.sources?.length ?? 0) === 1 ? '' : 's' }}.
                </p>
              </div>
              <div class="md" v-html="previewHtml" />
            </div>
          </section>
        </div>

        <!-- Conteúdo usado para PDF -->
        <section v-if="result" class="pdf-only">
          <div id="pdf-root" class="pdf-page">
            <header class="pdf-header">
              <div class="pdf-brand">Studies Assistant</div>
              <div class="pdf-title">{{ result.title }}</div>
              <div class="pdf-sub">{{ kindLabel(result.kind) }} · Gerado a partir dos seus PDFs</div>
            </header>
            <div class="pdf-body md" v-html="previewHtml" />
            <footer class="pdf-footer">
              <div class="pdf-foot-left">Fontes: {{ result.sources?.length ?? 0 }} trechos</div>
              <div class="pdf-foot-right">{{ new Date().toLocaleDateString('pt-BR') }}</div>
            </footer>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<style scoped>
.mat-layout { display: flex; height: 100vh; background: var(--bg); }

.mat-sidebar {
  width: 220px;
  flex-shrink: 0;
  background: var(--bg-2);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 0.75rem 0.5rem;
}
.mat-sidebar-top { display: flex; flex-direction: column; gap: 6px; flex: 1; }
.back-btn {
  display: flex; align-items: center; gap: 0.55rem;
  padding: 0.55rem 0.75rem;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-2);
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}
.back-btn:hover { background: var(--bg-hover); color: var(--text); }

.mat-sidebar-bottom { border-top: 1px solid var(--border); padding-top: 0.5rem; }
.sidebar-user {
  display: flex; align-items: center; gap: 0.6rem;
  padding: 0.55rem 0.75rem;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  cursor: pointer;
  width: 100%;
  transition: background 0.12s;
}
.sidebar-user:hover { background: var(--bg-hover); }
.user-avatar {
  width: 26px; height: 26px; border-radius: 50%;
  background: var(--accent); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.75rem; font-weight: 600; flex-shrink: 0;
}
.user-name {
  flex: 1; font-size: 0.875rem; color: var(--text-2);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

.mat-main { flex: 1; overflow-y: auto; padding: 1.75rem 1.5rem; }
.mat-content { max-width: 1100px; margin: 0 auto; }

.mat-title-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }
.mat-title { font-size: 1.45rem; font-weight: 650; color: var(--text); margin-bottom: 0.25rem; }
.mat-sub { font-size: 0.9rem; color: var(--text-2); line-height: 1.55; }
.mat-actions { display: flex; gap: 8px; flex-shrink: 0; }

.mat-grid {
  display: grid;
  grid-template-columns: 360px 320px 1fr;
  gap: 0.9rem;
  margin-top: 1.2rem;
  align-items: start;
}

.card {
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
}
.card-title { font-size: 0.9rem; font-weight: 650; color: var(--text); margin-bottom: 0.75rem; }
.card-title-row { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; margin-bottom: 0.65rem; }
.mini-actions { display: flex; align-items: center; gap: 0.45rem; font-size: 0.75rem; color: var(--text-3); }
.link {
  border: none; background: transparent; padding: 0;
  color: var(--accent); cursor: pointer; font-weight: 600; font-size: 0.75rem;
}
.dot { color: var(--border-strong); }
.badge {
  font-size: 0.72rem;
  color: var(--accent);
  border: 1px solid rgba(16, 163, 127, 0.35);
  background: rgba(16, 163, 127, 0.08);
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
}

.field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 0.8rem; }
.field label { font-size: 0.76rem; color: var(--text-3); }
.input, .textarea {
  width: 100%;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text);
  padding: 0.55rem 0.65rem;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.textarea { resize: vertical; min-height: 90px; }
.input:focus, .textarea:focus {
  border-color: var(--border-strong);
  box-shadow: 0 0 0 3px rgba(16, 163, 127, 0.07);
}

.segmented {
  display: flex;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 3px;
  gap: 4px;
}
.seg-btn {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--text-2);
  font-size: 0.82rem;
  padding: 0.45rem 0.55rem;
  border-radius: 999px;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}
.seg-btn:hover { background: var(--bg-hover); color: var(--text); }
.seg-btn.active { background: var(--bg-2); border: 1px solid var(--border); color: var(--text); }

.checkline { display: flex; align-items: center; gap: 0.55rem; font-size: 0.8rem; color: var(--text-2); margin: 0.25rem 0 0.75rem; }
.checkline input { accent-color: var(--accent); }

.doc-pick { list-style: none; display: flex; flex-direction: column; gap: 6px; margin: 0.25rem 0 0.6rem; padding: 0; max-height: 320px; overflow: auto; }
.doc-pick-item {
  display: flex; align-items: center; gap: 0.55rem;
  padding: 0.55rem 0.6rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--bg);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.doc-pick-item:hover { border-color: var(--border-strong); background: var(--bg-hover); }
.doc-check { pointer-events: none; }
.doc-name { font-size: 0.82rem; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.hint { font-size: 0.75rem; color: var(--text-3); line-height: 1.5; margin-top: 0.6rem; }

.preview-card { min-height: 520px; }
.preview { display: flex; flex-direction: column; gap: 0.8rem; }
.preview-top { border-bottom: 1px solid var(--border); padding-bottom: 0.75rem; }
.preview-title { font-size: 1.1rem; font-weight: 650; color: var(--text); margin-bottom: 0.2rem; }
.preview-meta { font-size: 0.75rem; color: var(--text-3); }
.preview-empty { padding: 1.5rem 0.75rem; }

.md :deep(h1), .md :deep(h2), .md :deep(h3) { color: var(--text); margin: 1rem 0 0.5rem; }
.md :deep(p) { color: var(--text-2); line-height: 1.75; margin: 0.45rem 0; }
.md :deep(ul), .md :deep(ol) { padding-left: 1.2rem; color: var(--text-2); }
.md :deep(li) { margin: 0.25rem 0; }
.md :deep(code) { background: var(--bg-3); padding: 0.15rem 0.3rem; border-radius: 6px; border: 1px solid var(--border); }
.md :deep(pre) { background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 0.75rem; overflow: auto; }
.md :deep(blockquote) { border-left: 3px solid var(--border-strong); padding-left: 0.75rem; color: var(--text-2); margin: 0.75rem 0; }
.md :deep(table) { width: 100%; border-collapse: collapse; margin: 0.75rem 0; }
.md :deep(th), .md :deep(td) { border: 1px solid var(--border); padding: 0.45rem 0.5rem; font-size: 0.85rem; }
.md :deep(th) { background: var(--bg-3); color: var(--text); text-align: left; }

.feedback-err { font-size: 0.82rem; color: var(--danger); margin-top: 0.4rem; }

.skeleton { display: flex; flex-direction: column; gap: 10px; margin-top: 0.5rem; }
.skel-row { height: 44px; border-radius: var(--radius); background: var(--bg-3); animation: pulse 1.5s ease-in-out infinite; }
.skel-row--sm { width: 70%; }
@keyframes pulse { 0%, 100% { opacity: 0.45; } 50% { opacity: 0.85; } }

.empty { color: var(--text-3); font-size: 0.85rem; padding: 0.75rem 0.25rem; }

/* PDF rendering */
.pdf-only { position: absolute; left: -99999px; top: 0; width: 0; height: 0; overflow: hidden; }
.pdf-page {
  width: 210mm;
  min-height: 297mm;
  background: #fff;
  color: #0b1220;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  padding: 14mm 14mm 16mm;
}
.pdf-header { border-bottom: 1px solid #e6eaf0; padding-bottom: 6mm; margin-bottom: 6mm; }
.pdf-brand { font-size: 10pt; letter-spacing: 0.08em; color: #5a667a; font-weight: 700; text-transform: uppercase; }
.pdf-title { font-size: 20pt; font-weight: 750; margin-top: 2mm; }
.pdf-sub { font-size: 10pt; color: #5a667a; margin-top: 2mm; }
.pdf-body { font-size: 11pt; }
.pdf-body :deep(p) { color: #22304a; }
.pdf-body :deep(h1), .pdf-body :deep(h2), .pdf-body :deep(h3) { color: #0b1220; }
.pdf-body :deep(code) { background: #f3f5f8; border: 1px solid #e6eaf0; }
.pdf-body :deep(pre) { background: #f9fafb; border: 1px solid #e6eaf0; }
.pdf-footer {
  border-top: 1px solid #e6eaf0;
  margin-top: 8mm;
  padding-top: 4mm;
  display: flex;
  justify-content: space-between;
  font-size: 9pt;
  color: #5a667a;
}

@media (max-width: 980px) {
  .mat-grid { grid-template-columns: 1fr; }
  .mat-actions { width: 100%; justify-content: flex-start; }
}
@media (max-width: 600px) {
  .mat-sidebar { display: none; }
  .mat-main { padding: 1.25rem 1rem; }
}
</style>

