<script setup lang="ts">
import { useAuth } from '@/composables/useAuth'
import { useLogout } from '@/composables/useLogout'
import { userInitial } from '@/lib/format'

const { user } = useAuth()
const { onLogout } = useLogout()
</script>

<template>
  <button class="sidebar-user" type="button" @click="onLogout">
    <div class="user-avatar">{{ userInitial(user?.username) }}</div>
    <span class="user-name">{{ user?.username }}</span>
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>
    </svg>
  </button>
</template>

<style scoped>
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
  text-align: left;
}
</style>
