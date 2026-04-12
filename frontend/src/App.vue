<script setup lang="ts">
import { onMounted, ref } from 'vue'

/** Base da API Django (dev: runserver na porta 8000) */
const API_BASE = 'http://127.0.0.1:8000'

const healthStatus = ref<string | null>(null)
const healthError = ref<string | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await fetch(`${API_BASE}/api/health/`)
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`)
    }
    const data = (await res.json()) as { status: string }
    healthStatus.value = data.status
  } catch (e) {
    healthError.value = e instanceof Error ? e.message : 'Erro desconhecido'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <main class="page">
    <h1>Studies Assistant</h1>
    <section class="api" aria-live="polite">
      <p v-if="loading">A contactar o backend…</p>
      <p v-else-if="healthError" class="err">
        Não foi possível ligar à API: {{ healthError }}
      </p>
      <p v-else>
        Backend <code>/api/health/</code>:
        <strong>{{ healthStatus }}</strong>
      </p>
    </section>
  </main>
</template>

<style scoped>
.page {
  max-width: 40rem;
  margin: 0 auto;
  padding: 2rem;
  font-family: system-ui, sans-serif;
}

h1 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

.api {
  padding: 1rem;
  border-radius: 8px;
  background: #f4f4f5;
}

.err {
  color: #b91c1c;
}

code {
  font-size: 0.9em;
}
</style>
