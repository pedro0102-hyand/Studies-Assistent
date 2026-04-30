<script setup lang="ts">
import { nextTick, onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch } from '@/lib/api'
import { useAuth } from '@/composables/useAuth'
import ThemeToggle from '@/components/ThemeToggle.vue'

export interface ApiConversation {
  id: number
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export interface ApiChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  sources: Array<{
    document_id: number
    chunk_index: number
    original_name: string
    excerpt: string
  }>
  created_at: string
}

const router = useRouter()
const { user, logout } = useAuth()

const conversations = ref<ApiConversation[]>([])
const selectedId = ref<number | null>(null)
const messages = ref<ApiChatMessage[]>([])
const input = ref('')
const listLoading = ref(true)
const messagesLoading = ref(false)
const sendPending = ref(false)
const sendError = ref<string | null>(null)
const listError = ref<string | null>(null)
const messagesEnd = ref<HTMLElement | null>(null)
const composeRef = ref<HTMLTextAreaElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const sidebarOpen = ref(true)
const showSources = ref<number | null>(null)
const attachedFile = ref<File | null>(null)

// Renomear conversa
const renamingId = ref<number | null>(null)
const renameValue = ref('')
const renameInputRef = ref<HTMLInputElement | null>(null)

const selectedConv = computed(() =>
  conversations.value.find((c) => c.id === selectedId.value)
)

// ── Conversas ──────────────────────────────────────────────
async function loadConversations() {
  listLoading.value = true
  listError.value = null
  try {
    const res = await apiFetch('/api/chat/conversations/')
    if (!res.ok) throw new Error(`Erro ${res.status}`)
    conversations.value = (await res.json()) as ApiConversation[]
  } catch (e) {
    listError.value = e instanceof Error ? e.message : 'Erro ao carregar'
    conversations.value = []
  } finally {
    listLoading.value = false
  }
}

async function loadMessages(id: number) {
  messagesLoading.value = true
  sendError.value = null
  messages.value = []
  try {
    const res = await apiFetch(`/api/chat/conversations/${id}/messages/`)
    if (!res.ok) throw new Error(`Erro ${res.status}`)
    messages.value = (await res.json()) as ApiChatMessage[]
    await nextTick()
    scrollBottom()
  } finally {
    messagesLoading.value = false
  }
}

function selectConversation(id: number) {
  if (renamingId.value !== null) cancelRename()
  selectedId.value = id
  void loadMessages(id)
  if (window.innerWidth < 700) sidebarOpen.value = false
  nextTick(() => composeRef.value?.focus())
}

async function newConversation() {
  sendError.value = null
  try {
    const res = await apiFetch('/api/chat/conversations/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
    if (!res.ok) throw new Error(`Erro ${res.status}`)
    const conv = (await res.json()) as ApiConversation
    await loadConversations()
    selectConversation(conv.id)
  } catch (e) {
    listError.value = e instanceof Error ? e.message : 'Erro ao criar'
  }
}

async function removeConversation(id: number, ev: Event) {
  ev.stopPropagation()
  if (!confirm('Apagar esta conversa?')) return
  try {
    await apiFetch(`/api/chat/conversations/${id}/`, { method: 'DELETE' })
    if (selectedId.value === id) {
      selectedId.value = null
      messages.value = []
    }
    await loadConversations()
  } catch {}
}

// ── Renomear ───────────────────────────────────────────────
function startRename(conv: ApiConversation, ev: Event) {
  ev.stopPropagation()
  renamingId.value = conv.id
  renameValue.value = conv.title || ''
  nextTick(() => {
    renameInputRef.value?.focus()
    renameInputRef.value?.select()
  })
}

function cancelRename() {
  renamingId.value = null
  renameValue.value = ''
}

async function confirmRename(id: number) {
  const title = renameValue.value.trim()
  renamingId.value = null
  if (!title) return
  try {
    const res = await apiFetch(`/api/chat/conversations/${id}/`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    })
    if (res.ok) {
      await loadConversations()
    } else {
      // Fallback local caso endpoint PATCH não exista
      const idx = conversations.value.findIndex((c) => c.id === id)
      const conv = idx !== -1 ? conversations.value[idx] : undefined
      if (conv) conv.title = title
    }
  } catch {
    const idx = conversations.value.findIndex((c) => c.id === id)
    const conv = idx !== -1 ? conversations.value[idx] : undefined
    if (conv) conv.title = title
  }
}

function onRenameKeydown(e: KeyboardEvent, id: number) {
  if (e.key === 'Enter') { e.preventDefault(); confirmRename(id) }
  if (e.key === 'Escape') cancelRename()
}

// ── Envio ──────────────────────────────────────────────────
async function send() {
  const id = selectedId.value
  const text = input.value.trim()
  if (!id || (!text && !attachedFile.value) || sendPending.value) return

  sendPending.value = true
  sendError.value = null

  const displayText = text || (attachedFile.value ? `[Arquivo: ${attachedFile.value.name}]` : '')
  const userMsg: ApiChatMessage = {
    id: Date.now(),
    role: 'user',
    content: displayText,
    sources: [],
    created_at: new Date().toISOString(),
  }
  messages.value = [...messages.value, userMsg]
  input.value = ''
  const sentFile = attachedFile.value
  attachedFile.value = null
  autoResize()
  await nextTick()
  scrollBottom()

  try {
    let res: Response
    if (sentFile) {
      const form = new FormData()
      if (text) form.append('content', text)
      else form.append('content', `[Arquivo: ${sentFile.name}]`)
      form.append('file', sentFile)
      res = await apiFetch(`/api/chat/conversations/${id}/messages/`, {
        method: 'POST',
        body: form,
      })
    } else {
      res = await apiFetch(`/api/chat/conversations/${id}/messages/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text }),
      })
    }

    const data = (await res.json().catch(() => ({}))) as {
      detail?: string
      user_message?: ApiChatMessage
      assistant_message?: ApiChatMessage
    }
    if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `Erro ${res.status}`)

    if (data.user_message && data.assistant_message) {
      messages.value = messages.value
        .filter((m) => m.id !== userMsg.id)
        .concat([data.user_message, data.assistant_message])
    } else {
      await loadMessages(id)
    }
    await loadConversations()
    await nextTick()
    scrollBottom()
  } catch (e) {
    sendError.value = e instanceof Error ? e.message : 'Erro ao enviar'
    messages.value = messages.value.filter((m) => m.id !== userMsg.id)
  } finally {
    sendPending.value = false
    nextTick(() => composeRef.value?.focus())
  }
}

// ── Anexo ──────────────────────────────────────────────────
function openFilePicker() {
  fileInputRef.value?.click()
}

function onFileSelected(ev: Event) {
  const el = ev.target as HTMLInputElement
  const file = el.files?.[0] ?? null
  el.value = ''
  if (!file) return
  if (file.size > 25 * 1024 * 1024) {
    sendError.value = 'Arquivo muito grande (máx. 25 MB).'
    return
  }
  attachedFile.value = file
}

// ── Helpers ────────────────────────────────────────────────
function scrollBottom() {
  messagesEnd.value?.scrollIntoView({ behavior: 'smooth' })
}

function autoResize() {
  const el = composeRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 180) + 'px'
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

async function onLogout() {
  await logout()
  router.push('/login')
}

onMounted(() => { void loadConversations() })
</script>

<template>
  <div class="chat-layout" :class="{ 'sidebar-closed': !sidebarOpen }">

    <!-- ── Sidebar ── -->
    <aside class="sidebar">
      <div class="sidebar-top">
        <button class="icon-btn" title="Fechar menu" @click="sidebarOpen = false">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>
        <span class="sidebar-brand">Studies</span>
        <button class="icon-btn" title="Nova conversa" @click="newConversation">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 5v14M5 12h14"/>
          </svg>
        </button>
      </div>

      <nav class="conv-list-wrap">
        <div v-if="listLoading" class="conv-skeleton">
          <span class="skel"/><span class="skel skel--sm"/><span class="skel"/>
        </div>
        <p v-else-if="listError" class="conv-empty conv-empty--err">{{ listError }}</p>
        <p v-else-if="conversations.length === 0" class="conv-empty">Nenhuma conversa ainda.</p>
        <ul v-else class="conv-list">
          <li
            v-for="c in conversations"
            :key="c.id"
            class="conv-item"
            :class="{ active: selectedId === c.id }"
            @click="selectConversation(c.id)"
          >
            <input
              v-if="renamingId === c.id"
              ref="renameInputRef"
              v-model="renameValue"
              class="rename-input"
              @keydown="onRenameKeydown($event, c.id)"
              @blur="confirmRename(c.id)"
              @click.stop
            />
            <template v-else>
              <span class="conv-title">{{ c.title || 'Nova conversa' }}</span>
              <div class="conv-actions">
                <button class="conv-btn" title="Renomear" @click="startRename(c, $event)">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                </button>
                <button class="conv-btn conv-btn--del" title="Apagar" @click="removeConversation(c.id, $event)">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>
                  </svg>
                </button>
              </div>
            </template>
          </li>
        </ul>
      </nav>

      <div class="sidebar-bottom">
        <button class="sidebar-nav-item" @click="router.push('/documents')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          Meus PDFs
        </button>
        <button class="sidebar-nav-item" @click="router.push('/materials')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            <path d="M8 7h9M8 11h9M8 15h7"/>
          </svg>
          Materiais
        </button>
        <div class="sidebar-theme">
          <ThemeToggle />
        </div>
        <button class="sidebar-user" @click="onLogout">
          <div class="user-avatar">{{ user?.username?.[0]?.toUpperCase() ?? '?' }}</div>
          <span class="user-name">{{ user?.username }}</span>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>
          </svg>
        </button>
      </div>
    </aside>

    <!-- ── Botão flutuante reabrir sidebar (desktop) ── -->
    <Transition name="fade">
      <button
        v-if="!sidebarOpen"
        class="sidebar-reopen"
        title="Abrir menu"
        @click="sidebarOpen = true"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button>
    </Transition>

    <!-- ── Área principal ── -->
    <div class="main-area">

      <!-- Topbar (mobile) -->
      <header class="topbar">
        <button class="icon-btn" @click="sidebarOpen = !sidebarOpen">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>
        <span class="topbar-title">{{ selectedConv?.title || 'Studies Assistant' }}</span>
        <button class="icon-btn" @click="newConversation">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 5v14M5 12h14"/>
          </svg>
        </button>
      </header>

      <!-- Mensagens -->
      <div class="messages-area">

        <!-- Boas-vindas -->
        <div v-if="selectedId === null" class="welcome">
          <div class="welcome-icon">
            <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <h1 class="welcome-title">Studies Assistant</h1>
          <p class="welcome-sub">Seu assistente de estudos com IA. Faça perguntas e obtenha respostas baseadas nos seus próprios documentos.</p>

          <div class="welcome-cards">
            <div class="welcome-card">
              <div class="wcard-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
              </div>
              <h3>Envie seus PDFs</h3>
              <p>Faça upload dos seus materiais em <strong>Meus PDFs</strong>. O conteúdo é indexado automaticamente.</p>
            </div>
            <div class="welcome-card">
              <div class="wcard-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
              </div>
              <h3>Pergunte e explore</h3>
              <p>Faça perguntas sobre o conteúdo. A IA busca respostas diretamente nos seus documentos.</p>
            </div>
            <div class="welcome-card">
              <div class="wcard-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              <h3>Histórico organizado</h3>
              <p>Todas as conversas ficam salvas na barra lateral e podem ser renomeadas a qualquer hora.</p>
            </div>
          </div>

          <button class="btn-primary-cta" @click="newConversation">
            Iniciar nova conversa
          </button>
        </div>

        <!-- Loading mensagens -->
        <div v-else-if="messagesLoading" class="messages-loading">
          <span class="typing-dot"/><span class="typing-dot"/><span class="typing-dot"/>
        </div>

        <!-- Lista de mensagens -->
        <div v-else class="messages-list">
          <p v-if="messages.length === 0" class="msgs-empty">
            Envie uma mensagem para começar. As respostas são baseadas nos seus PDFs.
          </p>

          <div
            v-for="m in messages"
            :key="m.id"
            class="msg-row"
            :class="m.role"
          >
            <div v-if="m.role === 'assistant'" class="msg-avatar assistant-avatar">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="12" cy="12" r="10"/>
                <path d="M8 12l3 3 5-5" stroke="white" stroke-width="2" fill="none"/>
              </svg>
            </div>
            <div class="msg-content">
              <div class="msg-bubble">{{ m.content }}</div>
              <div v-if="m.role === 'assistant' && m.sources?.length" class="sources-wrap">
                <button class="sources-toggle" @click="showSources = showSources === m.id ? null : m.id">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16h16V8z"/>
                  </svg>
                  {{ m.sources.length }} fonte{{ m.sources.length > 1 ? 's' : '' }}
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                    :style="{ transform: showSources === m.id ? 'rotate(180deg)' : 'none', transition: 'transform .2s' }">
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </button>
                <div v-if="showSources === m.id" class="sources-list">
                  <div v-for="(s, i) in m.sources" :key="i" class="source-item">
                    <div class="source-header">
                      <span class="source-name">{{ s.original_name }}</span>
                      <span class="source-chunk">chunk {{ s.chunk_index }}</span>
                    </div>
                    <p class="source-excerpt">{{ s.excerpt }}</p>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="m.role === 'user'" class="msg-avatar user-avatar-sm">
              {{ user?.username?.[0]?.toUpperCase() ?? '?' }}
            </div>
          </div>

          <!-- Digitando... -->
          <div v-if="sendPending" class="msg-row assistant">
            <div class="msg-avatar assistant-avatar">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10"/></svg>
            </div>
            <div class="msg-content">
              <div class="msg-bubble typing-bubble">
                <span class="typing-dot"/><span class="typing-dot"/><span class="typing-dot"/>
              </div>
            </div>
          </div>

          <div ref="messagesEnd"/>
        </div>
      </div>

      <!-- Compose -->
      <div v-if="selectedId !== null" class="compose-area">
        <p v-if="sendError" class="compose-error" role="alert">{{ sendError }}</p>

        <!-- Arquivo anexado -->
        <div v-if="attachedFile" class="attach-preview">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          <span>{{ attachedFile.name }}</span>
          <button class="attach-remove" @click="attachedFile = null">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div class="compose-box">
          <input ref="fileInputRef" type="file" accept=".pdf,.doc,.docx,.txt,.md" class="sr-only" @change="onFileSelected"/>

          <button class="compose-icon-btn" title="Anexar arquivo" :disabled="sendPending" @click="openFilePicker">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
            </svg>
          </button>

          <textarea
            ref="composeRef"
            v-model="input"
            class="compose-input"
            placeholder="Escreva sua mensagem..."
            rows="1"
            :disabled="sendPending"
            @input="autoResize"
            @keydown="onKeydown"
          />

          <button
            class="compose-send"
            :class="{ active: (input.trim() || attachedFile) && !sendPending }"
            :disabled="(!input.trim() && !attachedFile) || sendPending"
            title="Enviar"
            @click="send"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="12" y1="19" x2="12" y2="5"/>
              <polyline points="5 12 12 5 19 12"/>
            </svg>
          </button>
        </div>
        <p class="compose-hint">Enter para enviar · Shift+Enter para nova linha</p>
      </div>
    </div>

    <!-- Overlay mobile -->
    <div v-if="sidebarOpen && isMobile" class="sidebar-overlay" @click="sidebarOpen = false"/>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
export default defineComponent({ name: 'ChatView' })
const isMobile = typeof window !== 'undefined' && window.innerWidth < 700
</script>

<style scoped>
/* ── Transição do botão reabrir ── */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s, transform 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: scale(0.85); }

/* ── Layout ── */
.chat-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--bg);
  position: relative;
}

/* ── Sidebar ── */
.sidebar {
  width: var(--sidebar-w);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-2);
  border-right: 1px solid var(--border);
  height: 100vh;
  overflow: hidden;
  transition: width 0.22s cubic-bezier(0.4,0,0.2,1), opacity 0.2s, border-color 0.2s;
  position: relative;
  z-index: 20;
}

.chat-layout.sidebar-closed .sidebar {
  width: 0;
  opacity: 0;
  pointer-events: none;
  border-right-color: transparent;
}

.sidebar-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 0.75rem 0.5rem;
  flex-shrink: 0;
}

.sidebar-brand {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-2);
  letter-spacing: 0.03em;
}

/* ── Botão reabrir sidebar ── */
.sidebar-reopen {
  position: fixed;
  top: 0.875rem;
  left: 0.875rem;
  z-index: 30;
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--bg-2);
  color: var(--text-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.sidebar-reopen:hover {
  background: var(--bg-hover);
  color: var(--text);
  border-color: var(--border-strong);
}

/* ── Conversas ── */
.conv-list-wrap {
  flex: 1;
  overflow-y: auto;
  padding: 0.25rem 0.5rem;
}

.conv-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.conv-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 0.6rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.12s;
  min-width: 0;
}

.conv-item:hover { background: var(--bg-hover); }
.conv-item.active { background: var(--bg-active); }

.conv-title {
  flex: 1;
  font-size: 0.8375rem;
  color: var(--text-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-item.active .conv-title { color: var(--text); }

.conv-actions {
  display: none;
  align-items: center;
  gap: 1px;
  flex-shrink: 0;
}

.conv-item:hover .conv-actions,
.conv-item.active .conv-actions {
  display: flex;
}

.conv-btn {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--text-3);
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}

.conv-btn:hover { background: var(--bg-3); color: var(--text); }
.conv-btn--del:hover { color: var(--danger); background: var(--danger-bg); }

.rename-input {
  flex: 1;
  background: var(--bg-3);
  border: 1px solid var(--accent);
  border-radius: 4px;
  color: var(--text);
  font-size: 0.8375rem;
  padding: 0.15rem 0.4rem;
  outline: none;
  min-width: 0;
}

/* Skeleton */
.conv-skeleton { display: flex; flex-direction: column; gap: 6px; padding: 0.5rem; }
.skel {
  display: block;
  height: 30px;
  border-radius: var(--radius-sm);
  background: var(--bg-3);
  animation: pulse 1.5s ease-in-out infinite;
}
.skel--sm { width: 60%; }
@keyframes pulse {
  0%, 100% { opacity: 0.35; }
  50% { opacity: 0.7; }
}

.conv-empty { font-size: 0.8rem; color: var(--text-3); padding: 0.75rem; text-align: center; }
.conv-empty--err { color: var(--danger); }

/* ── Sidebar bottom ── */
.sidebar-bottom {
  padding: 0.5rem;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex-shrink: 0;
}

.sidebar-theme {
  padding: 0.35rem 0.45rem 0.45rem;
}

.sidebar-nav-item {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.5rem 0.6rem;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-2);
  font-size: 0.8375rem;
  cursor: pointer;
  text-align: left;
  transition: background 0.12s, color 0.12s;
}

.sidebar-nav-item:hover { background: var(--bg-hover); color: var(--text); }

.sidebar-user {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.5rem 0.6rem;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  cursor: pointer;
  width: 100%;
  transition: background 0.12s;
}
.sidebar-user:hover { background: var(--bg-hover); }

.user-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 700;
  flex-shrink: 0;
}

.user-name {
  flex: 1;
  font-size: 0.8375rem;
  color: var(--text-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Icon btn genérico ── */
.icon-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--text-2);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}
.icon-btn:hover { background: var(--bg-hover); color: var(--text); }

/* ── Main ── */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100vh;
  overflow: hidden;
}

/* ── Topbar (mobile) ── */
.topbar {
  display: none;
  align-items: center;
  justify-content: space-between;
  padding: 0 0.75rem;
  height: var(--header-h);
  border-bottom: 1px solid var(--border);
  background: var(--bg);
  flex-shrink: 0;
}

.topbar-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 55%;
}

/* ── Messages area ── */
.messages-area {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* ── Boas-vindas ── */
.welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1.5rem 3rem;
  text-align: center;
}

.welcome-icon {
  width: 62px;
  height: 62px;
  border-radius: 18px;
  background: var(--bg-3);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  margin-bottom: 1.25rem;
}

.welcome-title {
  font-size: 1.6rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 0.55rem;
}

.welcome-sub {
  font-size: 0.9375rem;
  color: var(--text-2);
  max-width: 30rem;
  line-height: 1.6;
  margin-bottom: 2rem;
}

.welcome-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  max-width: 620px;
  width: 100%;
  margin-bottom: 2rem;
}

.welcome-card {
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  text-align: left;
  transition: border-color 0.15s;
}

.welcome-card:hover { border-color: var(--border-strong); }

.wcard-icon { color: var(--accent); margin-bottom: 0.55rem; }

.welcome-card h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 0.3rem;
}

.welcome-card p {
  font-size: 0.8rem;
  color: var(--text-2);
  line-height: 1.5;
}

.welcome-card strong { color: var(--text); font-weight: 500; }

.btn-primary-cta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.6rem 1.5rem;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-primary-cta:hover { background: var(--accent-hover); }

/* ── Loading ── */
.messages-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  flex: 1;
}

/* ── Messages list ── */
.messages-list {
  max-width: 48rem;
  width: 100%;
  margin: 0 auto;
  padding: 1.5rem 1rem 0.5rem;
  display: flex;
  flex-direction: column;
}

.msgs-empty {
  padding: 3rem 1rem;
  text-align: center;
  color: var(--text-3);
  font-size: 0.875rem;
}

/* ── Mensagens ── */
.msg-row {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem 0;
  align-items: flex-start;
}

.msg-row.user { flex-direction: row-reverse; }

.msg-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 700;
  margin-top: 2px;
}

.assistant-avatar { background: var(--accent); color: #fff; }

.user-avatar-sm {
  background: var(--bg-3);
  color: var(--text-2);
  border: 1px solid var(--border);
  font-size: 0.72rem;
  font-weight: 700;
}

.msg-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  max-width: calc(100% - 76px);
}

.msg-row.user .msg-content { align-items: flex-end; }

.msg-bubble {
  font-size: 0.9375rem;
  line-height: 1.65;
  color: var(--text);
  white-space: pre-wrap;
  word-break: break-word;
}

.msg-row.assistant .msg-bubble {
  color: var(--text);
}

.msg-row.user .msg-bubble {
  background: var(--bg-3);
  border: 1px solid var(--border);
  border-radius: 14px 14px 4px 14px;
  padding: 0.6rem 0.875rem;
  display: inline-block;
}

.typing-bubble {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 0.6rem 0.875rem;
}

/* ── Fontes ── */
.sources-wrap { display: flex; flex-direction: column; gap: 0.4rem; }

.sources-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.72rem;
  color: var(--text-3);
  background: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.2rem 0.5rem;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}

.sources-toggle:hover { background: var(--bg-3); color: var(--text-2); }

.sources-list { display: flex; flex-direction: column; gap: 5px; }

.source-item {
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.5rem 0.65rem;
}

.source-header { display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.25rem; }
.source-name { font-size: 0.72rem; font-weight: 600; color: var(--accent); }
.source-chunk { font-size: 0.68rem; color: var(--text-3); }
.source-excerpt { font-size: 0.78rem; color: var(--text-2); line-height: 1.45; }

/* ── Typing dots ── */
.typing-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-3);
  animation: blink 1.2s ease-in-out infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.85); }
  40% { opacity: 1; transform: scale(1); }
}

/* ── Compose ── */
.compose-area {
  padding: 0.6rem 1rem 0.9rem;
  background: var(--bg);
  flex-shrink: 0;
  border-top: 1px solid var(--border);
}

.compose-error {
  font-size: 0.78rem;
  color: var(--danger);
  margin-bottom: 0.4rem;
  max-width: 48rem;
  margin-left: auto;
  margin-right: auto;
  padding: 0 0.25rem;
}

.attach-preview {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  max-width: 48rem;
  margin: 0 auto 0.4rem;
  padding: 0.3rem 0.6rem;
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.78rem;
  color: var(--text-2);
}

.attach-preview svg { color: var(--accent); flex-shrink: 0; }
.attach-preview span { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.attach-remove {
  border: none;
  background: transparent;
  color: var(--text-3);
  cursor: pointer;
  display: flex;
  align-items: center;
  border-radius: 3px;
  padding: 2px;
  transition: color 0.12s, background 0.12s;
}
.attach-remove:hover { color: var(--danger); background: var(--danger-bg); }

.compose-box {
  display: flex;
  align-items: flex-end;
  gap: 0.3rem;
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 0.4rem 0.4rem 0.4rem 0.6rem;
  max-width: 48rem;
  margin: 0 auto;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.compose-box:focus-within {
  border-color: var(--border-strong);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.compose-icon-btn {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  border-radius: 7px;
  border: none;
  background: transparent;
  color: var(--text-3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
  margin-bottom: 1px;
}
.compose-icon-btn:hover:not(:disabled) { background: var(--bg-hover); color: var(--text); }
.compose-icon-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.compose-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text);
  font-size: 0.9375rem;
  line-height: 1.5;
  resize: none;
  max-height: 180px;
  padding: 0.28rem 0;
  overflow-y: auto;
}
.compose-input::placeholder { color: var(--text-3); }

.compose-send {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: none;
  background: var(--bg-3);
  color: var(--text-3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  margin-bottom: 1px;
}
.compose-send.active { background: var(--accent); color: #fff; }
.compose-send:disabled { opacity: 0.4; cursor: not-allowed; }

.compose-hint {
  font-size: 0.7rem;
  color: var(--text-3);
  text-align: center;
  margin-top: 0.35rem;
  max-width: 48rem;
  margin-left: auto;
  margin-right: auto;
}

/* ── Overlay mobile ── */
.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.55);
  z-index: 10;
}

/* ── Responsivo ── */
@media (max-width: 700px) {
  .sidebar {
    position: fixed;
    top: 0; left: 0;
    height: 100vh;
    z-index: 50;
    width: var(--sidebar-w) !important;
    opacity: 1 !important;
    pointer-events: auto !important;
    transform: translateX(0);
    transition: transform 0.22s cubic-bezier(0.4,0,0.2,1);
    border-right-color: var(--border) !important;
  }

  .chat-layout.sidebar-closed .sidebar {
    transform: translateX(-100%);
    pointer-events: none !important;
  }

  .topbar { display: flex; }
  .sidebar-reopen { display: none !important; }

  .welcome-cards { grid-template-columns: 1fr; }
  .messages-list { padding: 1rem 0.75rem 0.5rem; }
  .compose-area { padding: 0.5rem 0.75rem 0.75rem; }
}

@media (min-width: 701px) {
  .topbar { display: none; }
}

.sr-only {
  position: absolute;
  width: 1px; height: 1px;
  padding: 0; margin: -1px;
  overflow: hidden;
  clip: rect(0,0,0,0);
  border: 0;
}
</style>
