<script setup lang="ts">
import { RouterLink } from 'vue-router'
import AppUserMenu from '@/components/AppUserMenu.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'

export interface SidebarLink {
  to: string
  label: string
}

defineProps<{
  links: SidebarLink[]
}>()
</script>

<template>
  <aside class="app-sidebar">
    <div class="app-sidebar-top">
      <RouterLink
        v-for="link in links"
        :key="link.to"
        :to="link.to"
        class="nav-link"
      >
        <slot :name="`icon-${link.to}`" />
        {{ link.label }}
      </RouterLink>
      <div class="app-sidebar-theme">
        <ThemeToggle />
      </div>
    </div>
    <div class="app-sidebar-bottom">
      <AppUserMenu />
    </div>
  </aside>
</template>

<style scoped>
.app-sidebar {
  width: 200px;
  flex-shrink: 0;
  background: var(--bg-2);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 0.75rem 0.5rem;
}

.app-sidebar-top {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-sm);
  color: var(--text-2);
  font-size: 0.875rem;
  text-decoration: none;
  transition: background 0.12s, color 0.12s;
}

.nav-link:hover,
.nav-link.router-link-active {
  background: var(--bg-hover);
  color: var(--text);
}

.app-sidebar-bottom {
  border-top: 1px solid var(--border);
  padding-top: 0.5rem;
}

.app-sidebar-theme {
  padding: 0.35rem 0.45rem 0.45rem;
}

@media (max-width: 600px) {
  .app-sidebar {
    display: none;
  }
}
</style>
