<script setup lang="ts">
import { computed } from 'vue'
import { useTheme } from '@/composables/useTheme'

const { theme, toggleTheme } = useTheme()
const isLight = computed(() => theme.value === 'light')
</script>

<template>
  <button class="theme-toggle" type="button" :title="isLight ? 'Ativar tema escuro' : 'Ativar tema claro'" @click="toggleTheme">
    <svg v-if="isLight" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>
    <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="12" cy="12" r="5"/>
      <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
    </svg>
    <span class="theme-label">{{ isLight ? 'Escuro' : 'Claro' }}</span>
  </button>
</template>

<style scoped>
.theme-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.45rem 0.6rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--bg-2);
  color: var(--text-2);
  font-size: 0.78rem;
  cursor: pointer;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
}
.theme-toggle:hover {
  background: var(--bg-hover);
  color: var(--text);
  border-color: var(--border-strong);
}
.theme-toggle:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px var(--accent-soft);
}
.theme-label {
  font-weight: 600;
}
</style>

