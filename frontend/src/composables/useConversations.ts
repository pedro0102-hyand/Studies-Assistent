import { nextTick, ref } from 'vue'
import { apiFetch } from '@/lib/api'
import { fetchAllPaginatedResults } from '@/lib/paginatedList'
import type { ApiConversation } from '@/types/api'

export function useConversations() {
  const conversations = ref<ApiConversation[]>([])
  const selectedId = ref<number | null>(null)
  const listLoading = ref(true)
  const listError = ref<string | null>(null)

  const renamingId = ref<number | null>(null)
  const renameValue = ref('')
  const renameInputRef = ref<HTMLInputElement | null>(null)

  const deleteConfirmOpen = ref(false)
  const deleteTargetId = ref<number | null>(null)

  async function loadConversations() {
    listLoading.value = true
    listError.value = null
    try {
      conversations.value = await fetchAllPaginatedResults<ApiConversation>(
        '/api/chat/conversations/',
        50,
      )
    } catch (e) {
      listError.value = e instanceof Error ? e.message : 'Erro ao carregar'
      conversations.value = []
    } finally {
      listLoading.value = false
    }
  }

  async function newConversation(onCreated?: (id: number) => void) {
    try {
      const res = await apiFetch('/api/chat/conversations/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })
      if (!res.ok) throw new Error(`Erro ${res.status}`)
      const conv = (await res.json()) as ApiConversation
      await loadConversations()
      selectedId.value = conv.id
      onCreated?.(conv.id)
      return conv.id
    } catch (e) {
      listError.value = e instanceof Error ? e.message : 'Erro ao criar'
      return null
    }
  }

  function selectConversation(id: number) {
    if (renamingId.value !== null) cancelRename()
    selectedId.value = id
    return id
  }

  function requestDeleteConversation(id: number, ev: Event) {
    ev.stopPropagation()
    deleteTargetId.value = id
    deleteConfirmOpen.value = true
  }

  async function confirmDeleteConversation(onDeleted?: () => void) {
    const id = deleteTargetId.value
    deleteConfirmOpen.value = false
    deleteTargetId.value = null
    if (!id) return
    try {
      await apiFetch(`/api/chat/conversations/${id}/`, { method: 'DELETE' })
      if (selectedId.value === id) {
        selectedId.value = null
        onDeleted?.()
      }
      await loadConversations()
    } catch {
      /* ignore */
    }
  }

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
    if (e.key === 'Enter') {
      e.preventDefault()
      void confirmRename(id)
    }
    if (e.key === 'Escape') cancelRename()
  }

  return {
    conversations,
    selectedId,
    listLoading,
    listError,
    renamingId,
    renameValue,
    renameInputRef,
    deleteConfirmOpen,
    deleteTargetId,
    loadConversations,
    newConversation,
    selectConversation,
    requestDeleteConversation,
    confirmDeleteConversation,
    startRename,
    cancelRename,
    confirmRename,
    onRenameKeydown,
  }
}
