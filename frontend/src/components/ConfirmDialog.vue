<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

type Variant = 'danger' | 'primary'

const props = defineProps<{
  open: boolean
  title: string
  description?: string
  confirmText?: string
  cancelText?: string
  variant?: Variant
}>()

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
  (e: 'update:open', v: boolean): void
}>()

const mounted = ref(false)
const confirmVariant = computed<Variant>(() => props.variant ?? 'danger')

function close() {
  emit('update:open', false)
  emit('cancel')
}

function confirm() {
  emit('update:open', false)
  emit('confirm')
}

function onKeydown(e: KeyboardEvent) {
  if (!props.open) return
  if (e.key === 'Escape') {
    e.preventDefault()
    close()
  }
}

watch(
  () => props.open,
  (v) => {
    if (typeof document === 'undefined') return
    if (v) document.body.style.overflow = 'hidden'
    else document.body.style.overflow = ''
  },
)

onMounted(() => {
  mounted.value = true
  if (typeof window !== 'undefined') window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') window.removeEventListener('keydown', onKeydown)
  if (typeof document !== 'undefined') document.body.style.overflow = ''
})
</script>

<template>
  <Teleport v-if="mounted" to="body">
    <Transition name="cd-fade">
      <div v-if="open" class="cd-overlay" @click.self="close">
        <div class="cd-modal" role="dialog" aria-modal="true" :aria-label="title">
          <div class="cd-top">
            <div class="cd-icon" :class="confirmVariant">
              <svg v-if="confirmVariant === 'danger'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.3 3.7h3.4L22 12l-8.3 8.3h-3.4L2 12l8.3-8.3z"/>
              </svg>
              <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 20h9"/><path d="M12 4h9"/><path d="M4 9h16"/><path d="M4 15h16"/>
              </svg>
            </div>
            <div class="cd-head">
              <h3 class="cd-title">{{ title }}</h3>
              <p v-if="description" class="cd-desc">{{ description }}</p>
            </div>
            <button class="cd-x" title="Fechar" @click="close">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          <div class="cd-actions">
            <button class="btn btn-secondary" @click="close">
              {{ cancelText ?? 'Cancelar' }}
            </button>
            <button
              class="btn"
              :class="confirmVariant === 'danger' ? 'btn-danger-solid' : 'btn-primary'"
              @click="confirm"
            >
              {{ confirmText ?? 'Confirmar' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.cd-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 9999;
}

.cd-modal {
  width: min(520px, 100%);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--bg-2);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.cd-top {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1rem 0.85rem;
  border-bottom: 1px solid var(--border);
}

.cd-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid var(--border);
  color: var(--text);
  background: var(--bg-3);
}
.cd-icon.danger {
  color: var(--danger);
  background: var(--danger-bg);
  border-color: rgba(229, 83, 75, 0.22);
}
.cd-icon.primary {
  color: var(--accent);
  background: var(--accent-soft);
  border-color: rgba(16, 163, 127, 0.22);
}

.cd-head { flex: 1; min-width: 0; }
.cd-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text);
  margin: 0;
}
.cd-desc {
  margin-top: 0.25rem;
  font-size: 0.85rem;
  color: var(--text-2);
  line-height: 1.5;
}

.cd-x {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-3);
  display: flex;
  align-items: center;
  justify-content: center;
}
.cd-x:hover { background: var(--bg-hover); color: var(--text); border-color: var(--border-strong); }

.cd-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 0.85rem 1rem 1rem;
}

.btn-danger-solid {
  background: var(--danger);
  color: #fff;
}
.btn-danger-solid:hover:not(:disabled) {
  background: color-mix(in srgb, var(--danger) 88%, #000);
}

.cd-fade-enter-active, .cd-fade-leave-active { transition: opacity .15s ease, transform .15s ease; }
.cd-fade-enter-from, .cd-fade-leave-to { opacity: 0; transform: translateY(6px) scale(.98); }
</style>

