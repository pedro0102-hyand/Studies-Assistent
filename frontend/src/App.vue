<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const { user, sessionReady, logout } = useAuth()

async function onLogout() {
  await logout()
}
</script>

<template>
  <div class="shell">
    <header class="header">
      <div class="header__inner">
        <RouterLink to="/" class="header__brand">
          <span class="header__logo" aria-hidden="true" />
          <span class="header__title">Studies Assistant</span>
        </RouterLink>

        <nav v-if="sessionReady" class="header__nav" aria-label="Principal">
          <RouterLink class="nav-link" to="/">Início</RouterLink>
          <template v-if="!user">
            <RouterLink class="nav-link" to="/login">Entrar</RouterLink>
            <RouterLink class="nav-link nav-link--cta" to="/register">Criar conta</RouterLink>
          </template>
          <template v-else>
            <RouterLink class="nav-link" to="/app">Área da app</RouterLink>
            <RouterLink class="nav-link" to="/documents">PDFs</RouterLink>
            <RouterLink class="nav-link" to="/chat">Chat</RouterLink>
            <button type="button" class="nav-link nav-link--logout" @click="onLogout">Sair</button>
          </template>
        </nav>
      </div>
    </header>

    <div class="shell__main">
      <RouterView />
    </div>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--sa-bg);
}

.shell__main {
  flex: 1;
  width: 100%;
}

.header {
  position: sticky;
  top: 0;
  z-index: 50;
  border-bottom: 1px solid var(--sa-border);
  background: color-mix(in srgb, var(--sa-surface) 88%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.header__inner {
  max-width: var(--sa-max);
  margin: 0 auto;
  padding: 0.65rem clamp(1rem, 4vw, 1.5rem);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem 1rem;
}

.header__brand {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  color: var(--sa-text);
  font-weight: 700;
  font-size: 1.05rem;
  letter-spacing: -0.02em;
  text-decoration: none;
}

.header__brand:hover {
  color: var(--sa-primary);
}

.header__logo {
  width: 2rem;
  height: 2rem;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--sa-primary), var(--sa-accent));
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.35);
}

.header__title {
  line-height: 1.2;
}

.header__nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 0.35rem;
  max-width: 100%;
}

.nav-link {
  padding: 0.45rem 0.85rem;
  border-radius: var(--sa-radius-full);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--sa-text-muted);
  text-decoration: none;
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
  transition:
    color 0.15s ease,
    background 0.15s ease,
    border-color 0.15s ease;
}

.nav-link:hover {
  color: var(--sa-text);
  background: var(--sa-primary-soft);
}

.nav-link.router-link-active:not(.nav-link--cta):not(.nav-link--logout) {
  color: var(--sa-primary);
  background: var(--sa-primary-soft);
}

.nav-link--cta {
  color: #fff;
  background: linear-gradient(135deg, var(--sa-primary), var(--sa-accent));
  box-shadow: 0 2px 10px rgba(79, 70, 229, 0.3);
}

.nav-link--cta:hover {
  color: #fff;
  filter: brightness(1.06);
}

.nav-link--logout {
  color: var(--sa-danger);
}

.nav-link--logout:hover {
  background: var(--sa-danger-bg);
  color: var(--sa-danger);
}

@media (max-width: 520px) {
  .header__inner {
    flex-direction: column;
    align-items: stretch;
  }

  .header__nav {
    justify-content: flex-start;
  }
}
</style>
