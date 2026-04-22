<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { apiFetch } from '@/lib/api'

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

const conversations = ref<ApiConversation[]>([])
const selectedId = ref<number | null>(null)
const messages = ref<ApiChatMessage[]>([])
const input = ref('')
const listLoading = ref(true)
const listError = ref<string | null>(null)
const messagesLoading = ref(false)
const sendPending = ref(false)
const sendError = ref<string | null>(null)
const messagesEnd = ref<HTMLElement | null>(null)
const composeInput = ref<HTMLTextAreaElement | null>(null)

async function loadConversations() {
  listError.value = null
  listLoading.value = true
  try {
    const res = await apiFetch('/api/chat/conversations/')
    if (!res.ok) {
      const d = (await res.json().catch(() => ({}))) as { detail?: string }
      throw new Error(d.detail ?? `Erro ${res.status}`)
    }
    conversations.value = (await res.json()) as ApiConversation[]
  } catch (e) {
    listError.value = e instanceof Error ? e.message : 'Falha ao carregar conversas'
    conversations.value = []
  } finally {
    listLoading.value = false
  }
}

async function loadMessages(id: number) {
  messagesLoading.value = true
  sendError.value = null
  try {
    const res = await apiFetch(`/api/chat/conversations/${id}/messages/`)
    if (!res.ok) {
      const d = (await res.json().catch(() => ({}))) as { detail?: string }
      throw new Error(d.detail ?? `Erro ${res.status}`)
    }
    messages.value = (await res.json()) as ApiChatMessage[]
    await nextTick()
    messagesEnd.value?.scrollIntoView({ behavior: 'smooth' })
  } catch (e) {
    sendError.value = e instanceof Error ? e.message : 'Falha ao carregar mensagens'
    messages.value = []
  } finally {
    messagesLoading.value = false
  }
}

function selectConversation(id: number) {
  selectedId.value = id
  void loadMessages(id)
  void nextTick(() => composeInput.value?.focus())
}

async function newConversation() {
  sendError.value = null
  try {
    const res = await apiFetch('/api/chat/conversations/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
    if (!res.ok) {
      const d = (await res.json().catch(() => ({}))) as { detail?: string }
      throw new Error(d.detail ?? `Erro ${res.status}`)
    }
    const conv = (await res.json()) as ApiConversation
    await loadConversations()
    selectConversation(conv.id)
    await nextTick(() => composeInput.value?.focus())
  } catch (e) {
    listError.value = e instanceof Error ? e.message : 'Falha ao criar conversa'
  }
}

async function removeConversation(id: number, ev: Event) {
  ev.stopPropagation()
  if (!confirm('Apagar esta conversa e todo o histórico?')) return
  try {
    const res = await apiFetch(`/api/chat/conversations/${id}/`, { method: 'DELETE' })
    if (!res.ok && res.status !== 204) {
      const d = (await res.json().catch(() => ({}))) as { detail?: string }
      throw new Error(d.detail ?? `Erro ${res.status}`)
    }
    if (selectedId.value === id) {
      selectedId.value = null
      messages.value = []
    }
    await loadConversations()
  } catch (e) {
    listError.value = e instanceof Error ? e.message : 'Falha ao apagar'
  }
}

async function send() {
  const id = selectedId.value
  const text = input.value.trim()
  if (!id || !text || sendPending.value) return

  sendPending.value = true
  sendError.value = null
  try {
    const res = await apiFetch(`/api/chat/conversations/${id}/messages/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: text }),
    })
    const data = (await res.json().catch(() => ({}))) as {
      detail?: string
      user_message?: ApiChatMessage
      assistant_message?: ApiChatMessage
    }
    if (!res.ok) {
      throw new Error(typeof data.detail === 'string' ? data.detail : `Erro ${res.status}`)
    }
    input.value = ''
    if (data.user_message && data.assistant_message) {
      messages.value = [...messages.value, data.user_message, data.assistant_message]
    } else {
      await loadMessages(id)
    }
    await loadConversations()
    await nextTick()
    messagesEnd.value?.scrollIntoView({ behavior: 'smooth' })
  } catch (e) {
    sendError.value = e instanceof Error ? e.message : 'Falha ao enviar'
  } finally {
    sendPending.value = false
    await nextTick(() => composeInput.value?.focus())
  }
}

function formatTime(iso: string) {
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
  void loadConversations()
})
</script>

<template>
  <div class="chat-page">
    <aside class="chat-sidebar sa-card sa-card--pad" aria-label="Conversas">
      <RouterLink class="sa-page__back chat__back" to="/app">
        <span aria-hidden="true">←</span> Área da app
      </RouterLink>

      <div class="chat-sidebar__head">
        <h1 class="chat-sidebar__title">Chat</h1>
        <button type="button" class="sa-btn sa-btn--primary chat-sidebar__new" @click="newConversation">
          Nova conversa
        </button>
      </div>

      <p v-if="listLoading" class="chat-muted">A carregar…</p>
      <p v-else-if="listError" class="chat-err">{{ listError }}</p>
      <p v-else-if="conversations.length === 0" class="chat-muted">Sem conversas. Cria uma nova.</p>
      <ul v-else class="chat-conv-list">
        <li
          v-for="c in conversations"
          :key="c.id"
          class="chat-conv-item"
          :class="{ 'chat-conv-item--active': selectedId === c.id }"
          @click="selectConversation(c.id)"
        >
          <div class="chat-conv-item__main">
            <span class="chat-conv-item__title">{{ c.title || `Conversa #${c.id}` }}</span>
            <span class="chat-conv-item__meta">{{ c.message_count }} mensagens</span>
          </div>
          <button
            type="button"
            class="chat-conv-item__del"
            title="Apagar conversa"
            @click="removeConversation(c.id, $event)"
          >
            ×
          </button>
        </li>
      </ul>
    </aside>

    <main class="chat-main sa-card sa-card--elevated">
      <template v-if="selectedId === null">
        <div class="chat-empty">
          <p class="chat-empty__title">Escolhe ou cria uma conversa</p>
          <p class="chat-muted">Usa a barra lateral para ver o histórico ou inicia uma nova conversa.</p>
        </div>
      </template>
      <template v-else>
        <div class="chat-main__header">
          <h2 class="chat-main__h2">
            {{ conversations.find((x) => x.id === selectedId)?.title || `Conversa #${selectedId}` }}
          </h2>
        </div>

        <div class="chat-messages" role="log" aria-live="polite">
          <p v-if="messagesLoading" class="chat-muted">A carregar mensagens…</p>
          <template v-else>
            <p v-if="messages.length === 0" class="chat-muted chat-messages__empty">
              Ainda sem mensagens. Escreve abaixo e envia — a resposta usa os teus PDFs (RAG).
            </p>
            <div
              v-for="m in messages"
              :key="m.id"
              class="chat-bubble"
              :class="m.role === 'user' ? 'chat-bubble--user' : 'chat-bubble--assistant'"
            >
              <span class="chat-bubble__role">{{ m.role === 'user' ? 'Tu' : 'Assistente' }}</span>
              <p class="chat-bubble__text">{{ m.content }}</p>
              <time class="chat-bubble__time" :datetime="m.created_at">{{ formatTime(m.created_at) }}</time>
              <ul v-if="m.role === 'assistant' && m.sources?.length" class="chat-sources">
                <li v-for="(s, i) in m.sources" :key="i" class="chat-sources__item">
                  <span class="chat-sources__meta">{{ s.original_name }} · chunk {{ s.chunk_index }}</span>
                  <p class="chat-sources__ex">{{ s.excerpt }}</p>
                </li>
              </ul>
            </div>
            <div ref="messagesEnd" />
          </template>
        </div>

        <div class="chat-compose">
          <p v-if="sendError" class="chat-err" role="alert">{{ sendError }}</p>
          <p class="chat-compose__hint">Enter envia · Shift+Enter nova linha</p>
          <div class="chat-compose__row">
            <textarea
              ref="composeInput"
              v-model="input"
              class="chat-compose__input"
              rows="2"
              placeholder="Escreve a tua pergunta…"
              :disabled="sendPending"
              @keydown.enter.exact.prevent="send"
            />
            <button
              type="button"
              class="sa-btn sa-btn--primary chat-compose__send"
              :disabled="!input.trim() || sendPending"
              @click="send"
            >
              {{ sendPending ? '…' : 'Enviar' }}
            </button>
          </div>
        </div>
      </template>
    </main>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  gap: 1rem;
  max-width: 56rem;
  margin: 0 auto;
  padding: 0 clamp(0.75rem, 3vw, 1.25rem) 2.5rem;
  min-height: calc(100vh - 4rem);
  align-items: stretch;
}

.chat__back {
  margin-bottom: 1rem;
  display: inline-block;
}

.chat-sidebar {
  flex: 0 0 min(260px, 34vw);
  display: flex;
  flex-direction: column;
  min-height: 18rem;
  max-height: calc(100vh - 5rem);
}

.chat-sidebar__head {
  margin-bottom: 0.75rem;
}

.chat-sidebar__title {
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0 0 0.5rem;
  color: var(--sa-text);
}

.chat-sidebar__new {
  width: 100%;
  font-size: 0.875rem;
}

.chat-conv-list {
  list-style: none;
  padding: 0;
  margin: 0;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.chat-conv-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.35rem;
  padding: 0.5rem 0.55rem;
  border-radius: var(--sa-radius-sm);
  border: 1px solid transparent;
  cursor: pointer;
  text-align: left;
}

.chat-conv-item:hover {
  background: color-mix(in srgb, var(--sa-primary) 6%, transparent);
}

.chat-conv-item--active {
  border-color: var(--sa-border);
  background: var(--sa-primary-soft);
}

.chat-conv-item__main {
  min-width: 0;
  flex: 1;
}

.chat-conv-item__title {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--sa-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-conv-item__meta {
  font-size: 0.72rem;
  color: var(--sa-text-muted);
}

.chat-conv-item__del {
  flex-shrink: 0;
  border: none;
  background: transparent;
  color: var(--sa-text-muted);
  font-size: 1.25rem;
  line-height: 1;
  padding: 0 0.15rem;
  cursor: pointer;
  border-radius: var(--sa-radius-sm);
}

.chat-conv-item__del:hover {
  color: var(--sa-danger);
  background: color-mix(in srgb, var(--sa-danger) 12%, transparent);
}

.chat-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 5rem);
}

.chat-main__header {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--sa-border);
}

.chat-main__h2 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--sa-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  text-align: center;
}

.chat-empty__title {
  font-weight: 700;
  color: var(--sa-text);
  margin: 0 0 0.35rem;
}

.chat-muted {
  color: var(--sa-text-muted);
  font-size: 0.9rem;
  margin: 0;
}

.chat-err {
  color: var(--sa-danger);
  font-size: 0.85rem;
  margin: 0 0 0.5rem;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem 1rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.chat-messages__empty {
  margin: 0.5rem 0 0;
  max-width: 28rem;
  line-height: 1.5;
}

.chat-bubble {
  max-width: 92%;
  padding: 0.65rem 0.85rem;
  border-radius: var(--sa-radius-sm);
  border: 1px solid var(--sa-border);
}

.chat-bubble--user {
  align-self: flex-end;
  background: color-mix(in srgb, var(--sa-primary) 14%, var(--sa-surface));
}

.chat-bubble--assistant {
  align-self: flex-start;
  background: var(--sa-surface);
}

.chat-bubble__role {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--sa-text-muted);
}

.chat-bubble__text {
  margin: 0.25rem 0 0.35rem;
  font-size: 0.9rem;
  line-height: 1.55;
  color: var(--sa-text);
  white-space: pre-wrap;
}

.chat-bubble__time {
  font-size: 0.7rem;
  color: var(--sa-text-muted);
}

.chat-sources {
  list-style: none;
  padding: 0.5rem 0 0;
  margin: 0.5rem 0 0;
  border-top: 1px dashed var(--sa-border);
}

.chat-sources__item {
  margin-bottom: 0.5rem;
}

.chat-sources__meta {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--sa-primary);
}

.chat-sources__ex {
  margin: 0.2rem 0 0;
  font-size: 0.75rem;
  color: var(--sa-text-muted);
  line-height: 1.4;
}

.chat-compose {
  padding: 0.75rem 1rem 1rem;
  border-top: 1px solid var(--sa-border);
}

.chat-compose__hint {
  font-size: 0.72rem;
  color: var(--sa-text-muted);
  margin: 0 0 0.4rem;
}

.chat-compose__row {
  display: flex;
  gap: 0.5rem;
  align-items: flex-end;
}

.chat-compose__input {
  flex: 1;
  resize: vertical;
  min-height: 2.75rem;
  max-height: 8rem;
  padding: 0.55rem 0.65rem;
  border-radius: var(--sa-radius-sm);
  border: 1px solid var(--sa-border);
  background: var(--sa-surface);
  color: var(--sa-text);
  font-size: 0.9rem;
  font-family: inherit;
}

.chat-compose__send {
  flex-shrink: 0;
}

@media (max-width: 720px) {
  .chat-page {
    flex-direction: column;
    max-height: none;
  }

  .chat-sidebar {
    flex: none;
    max-height: 40vh;
  }

  .chat-main {
    max-height: none;
    min-height: 50vh;
  }
}
</style>
