import { nextTick, onBeforeUnmount, ref, watch, type Ref } from 'vue'
import { apiFetch } from '@/lib/api'
import { readApiError } from '@/lib/format'
import { fetchAllPaginatedResults } from '@/lib/paginatedList'
import type { ApiChatMessage } from '@/types/api'

const ATTACH_MAX_BYTES = 25 * 1024 * 1024
const ATTACH_NAME_RE = /\.pdf$/i

export function useChatInput(options: { selectedId: Ref<number | null> }) {
  const attachedFile = ref<File | null>(null)
  const input = ref('')
  const sendError = ref<string | null>(null)
  const sendPending = ref(false)
  const composeRef = ref<HTMLTextAreaElement | null>(null)
  const fileDragOverlay = ref(false)
  const fileInputRef = ref<HTMLInputElement | null>(null)
  let fileDragDepth = 0

  function tryAttachFile(file: File | null): void {
    if (!file) return
    if (file.size > ATTACH_MAX_BYTES) {
      sendError.value = 'Arquivo muito grande (máx. 25 MB).'
      return
    }
    if (!ATTACH_NAME_RE.test(file.name)) {
      sendError.value = 'Formato não suportado. Apenas arquivos PDF.'
      return
    }
    sendError.value = null
    attachedFile.value = file
  }

  function openFilePicker() {
    fileInputRef.value?.click()
  }

  function onFileSelected(ev: Event) {
    const el = ev.target as HTMLInputElement
    const file = el.files?.[0] ?? null
    el.value = ''
    tryAttachFile(file)
  }

  function dataTransferHasFiles(dt: DataTransfer | null): boolean {
    return !!dt?.types?.includes('Files')
  }

  function onFileDragEnter(e: DragEvent) {
    if (options.selectedId.value === null || sendPending.value) return
    if (!dataTransferHasFiles(e.dataTransfer)) return
    e.preventDefault()
    fileDragDepth++
    fileDragOverlay.value = true
  }

  function onFileDragLeave(e: DragEvent) {
    if (options.selectedId.value === null) return
    if (!dataTransferHasFiles(e.dataTransfer)) return
    fileDragDepth--
    if (fileDragDepth < 0) fileDragDepth = 0
    if (fileDragDepth === 0) fileDragOverlay.value = false
  }

  function onFileDragOver(e: DragEvent) {
    if (options.selectedId.value === null || sendPending.value) return
    if (!dataTransferHasFiles(e.dataTransfer)) return
    e.preventDefault()
    if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy'
  }

  function onFileDrop(e: DragEvent) {
    fileDragDepth = 0
    fileDragOverlay.value = false
    if (options.selectedId.value === null || sendPending.value) return
    if (!dataTransferHasFiles(e.dataTransfer)) return
    e.preventDefault()
    const file = e.dataTransfer?.files?.[0] ?? null
    tryAttachFile(file)
  }

  function resetFileDragUi() {
    fileDragDepth = 0
    fileDragOverlay.value = false
  }

  watch(options.selectedId, resetFileDragUi)

  onBeforeUnmount(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('dragend', resetFileDragUi)
    }
  })

  if (typeof window !== 'undefined') {
    window.addEventListener('dragend', resetFileDragUi)
  }

  return {
    attachedFile,
    input,
    sendError,
    sendPending,
    composeRef,
    fileDragOverlay,
    fileInputRef,
    openFilePicker,
    onFileSelected,
    onFileDragEnter,
    onFileDragLeave,
    onFileDragOver,
    onFileDrop,
  }
}

export function useChatMessages(options: {
  selectedId: Ref<number | null>
  loadConversations: () => Promise<void>
  attachedFile: Ref<File | null>
  input: Ref<string>
  sendError: Ref<string | null>
  sendPending: Ref<boolean>
  composeRef: Ref<HTMLTextAreaElement | null>
}) {
  const messages = ref<ApiChatMessage[]>([])
  const messagesLoading = ref(false)
  const messagesEnd = ref<HTMLElement | null>(null)
  const showSources = ref<number | null>(null)

  function scrollBottom() {
    messagesEnd.value?.scrollIntoView({ behavior: 'smooth' })
  }

  function autoResize() {
    const el = options.composeRef.value
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 180) + 'px'
  }

  async function loadMessages(id: number) {
    messagesLoading.value = true
    options.sendError.value = null
    messages.value = []
    try {
      messages.value = await fetchAllPaginatedResults<ApiChatMessage>(
        `/api/chat/conversations/${id}/messages/`,
        100,
      )
      await nextTick()
      scrollBottom()
    } finally {
      messagesLoading.value = false
    }
  }

  async function send() {
    const id = options.selectedId.value
    const text = options.input.value.trim()
    if (!id || (!text && !options.attachedFile.value) || options.sendPending.value) return

    options.sendPending.value = true
    options.sendError.value = null

    const displayText = text || (options.attachedFile.value ? `[Arquivo: ${options.attachedFile.value.name}]` : '')
    const userMsg: ApiChatMessage = {
      id: Date.now(),
      role: 'user',
      content: displayText,
      sources: [],
      created_at: new Date().toISOString(),
    }
    messages.value = [...messages.value, userMsg]
    options.input.value = ''
    const sentFile = options.attachedFile.value
    options.attachedFile.value = null
    autoResize()
    await nextTick()
    scrollBottom()

    try {
      let res: Response
      if (sentFile) {
        const form = new FormData()
        if (text) form.append('content', text)
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
      if (!res.ok) {
        options.sendError.value = typeof data.detail === 'string' ? data.detail : await readApiError(res)
        if (data.user_message) {
          messages.value = messages.value
            .filter((m) => m.id !== userMsg.id)
            .concat([data.user_message])
        } else {
          messages.value = messages.value.filter((m) => m.id !== userMsg.id)
        }
        await options.loadConversations()
        await nextTick()
        scrollBottom()
        return
      }

      if (data.user_message && data.assistant_message) {
        messages.value = messages.value
          .filter((m) => m.id !== userMsg.id)
          .concat([data.user_message, data.assistant_message])
      } else {
        await loadMessages(id)
      }
      await options.loadConversations()
      await nextTick()
      scrollBottom()
    } catch (e) {
      options.sendError.value = e instanceof Error ? e.message : 'Erro ao enviar'
      messages.value = messages.value.filter((m) => m.id !== userMsg.id)
    } finally {
      options.sendPending.value = false
      nextTick(() => options.composeRef.value?.focus())
    }
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void send()
    }
  }

  function clearMessages() {
    messages.value = []
  }

  return {
    messages,
    messagesLoading,
    messagesEnd,
    showSources,
    loadMessages,
    send,
    onKeydown,
    autoResize,
    scrollBottom,
    clearMessages,
  }
}
