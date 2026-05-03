# Studies Assistant

> Assistente de estudos com IA que responde perguntas com base nos seus próprios PDFs — usando RAG (Retrieval-Augmented Generation) com Ollama, ChromaDB e uma interface Vue 3 moderna.

---

## Índice

- [Visão Geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Arquitetura](#arquitetura)
- [Tecnologias](#tecnologias)
- [Pré-requisitos](#pré-requisitos)
- [Instalação e Configuração](#instalação-e-configuração)
  - [1. Clonar o repositório](#1-clonar-o-repositório)
  - [2. Variáveis de ambiente](#2-variáveis-de-ambiente)
  - [3. Backend (Django)](#3-backend-django)
  - [4. Ollama (modelos de IA)](#4-ollama-modelos-de-ia)
  - [5. Frontend (Vue 3)](#5-frontend-vue-3)
  - [6. Celery (processamento assíncrono)](#6-celery-processamento-assíncrono)
- [Executar em Desenvolvimento](#executar-em-desenvolvimento)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Endpoints da API](#endpoints-da-api)
  - [Autenticação](#autenticação)
  - [Documentos](#documentos)
  - [RAG](#rag)
  - [Chat](#chat)
- [Pipeline RAG](#pipeline-rag)
- [Variáveis de Ambiente — Referência Completa](#variáveis-de-ambiente--referência-completa)
- [Comandos de Gestão Úteis](#comandos-de-gestão-úteis)
- [Deploy em Produção](#deploy-em-produção)
- [Contribuições](#contribuições)
- [Licença](#licença)

---

## Visão Geral

O **Studies Assistant** é uma aplicação full-stack que permite fazer upload de documentos PDF, indexá-los automaticamente com embeddings vetoriais e conversar com uma IA que responde exclusivamente com base no conteúdo dos seus próprios documentos. Cada utilizador tem o seu espaço isolado — os dados de um utilizador nunca aparecem nas respostas de outro.

```
Utilizador → Upload PDF → Extração de texto → Chunking → Embeddings (Ollama)
                ↓                                              ↓
           PostgreSQL                                      ChromaDB
                                                               ↓
Utilizador → Pergunta → Embedding da pergunta → Similarity search → LLM (Ollama) → Resposta
```

---

## Funcionalidades

- **Upload e gestão de PDFs** — carrega, lista e apaga documentos; estado de processamento em tempo real (polling).
- **RAG com isolamento por utilizador** — cada consulta ao ChromaDB é filtrada pelo `user_id`; impossível cruzar dados entre utilizadores.
- **Chat com histórico** — conversas persistidas no banco de dados; renomear, apagar e paginar conversas.
- **Anexo de PDF no chat** — envia um PDF diretamente numa mensagem; o texto é extraído e incluído no contexto do LLM.
- **Geração de materiais de estudo** — cria resumos, listas de exercícios e roadmaps a partir dos seus PDFs.
- **Exportação para PDF** — baixa qualquer material gerado como ficheiro PDF formatado.
- **Autenticação segura** — JWT armazenado em cookies HttpOnly (sem tokens expostos ao JavaScript); refresh automático.
- **Tema claro/escuro** — alternância persistida em `localStorage`.
- **Rate limiting** — throttling por IP nos endpoints de autenticação e por utilizador nos endpoints RAG/chat.

---

## Arquitetura

```
┌──────────────────────────────────────────────────────────────┐
│                        Frontend (Vue 3)                       │
│  LoginView · RegisterView · ChatView · DocumentsView         │
│  StudyMaterialsView · ThemeToggle · ConfirmDialog            │
└────────────────────────┬─────────────────────────────────────┘
                         │  HTTP / Proxy Vite (/api → :8000)
┌────────────────────────▼─────────────────────────────────────┐
│                     Django REST Framework                     │
│  core (auth, JWT cookies)  ·  documents (upload, RAG)        │
│  chat (conversas, mensagens)                                  │
└────────┬──────────────────────┬───────────────────────────────┘
         │                      │
   ┌─────▼──────┐        ┌──────▼───────┐        ┌─────────────┐
   │ PostgreSQL │        │   ChromaDB   │        │   Ollama    │
   │  (usuários,│        │  (vetores de │        │ nomic-embed │
   │  docs,     │        │   chunks,    │        │ gemma2:2b   │
   │  mensagens)│        │  filtro por  │        │ (ou outro)  │
   └────────────┘        │  user_id)    │        └─────────────┘
                         └──────────────┘
                                ▲
                   ┌────────────┴────────────┐
                   │  Celery Worker + Redis   │
                   │  (extração PDF assínc.)  │
                   └──────────────────────────┘
```

---

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Frontend | Vue 3, TypeScript, Vite, Vue Router |
| Estilo | CSS custom (variáveis, tema claro/escuro) |
| Backend | Django 5, Django REST Framework |
| Autenticação | SimpleJWT (cookies HttpOnly) |
| Base de dados | PostgreSQL (produção) / SQLite (desenvolvimento) |
| Vetor DB | ChromaDB (persistência local) |
| Embeddings | Ollama — `nomic-embed-text` |
| LLM | Ollama — `gemma2:2b` (configurável) |
| Extração PDF | pypdf |
| Fila de tarefas | Celery + Redis |
| HTTP client | httpx |
| Markdown | marked + DOMPurify |
| Export PDF | html2pdf.js |

---

## Pré-requisitos

- **Python** ≥ 3.11
- **Node.js** `^20.19.0` ou `≥ 22.12.0`
- **PostgreSQL** ≥ 14 (ou use SQLite para desenvolvimento rápido)
- **Redis** ≥ 6 (necessário para Celery em produção; opcional em dev — modo eager disponível)
- **[Ollama](https://ollama.com/)** instalado e em execução

---

## Instalação e Configuração

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-utilizador/studies-assistant.git
cd studies-assistant
```

### 2. Variáveis de ambiente

Crie um ficheiro `.env` na **raiz do repositório** (ou em `backend/`) com base no exemplo abaixo:

```dotenv
# ── Django ──────────────────────────────────────────────────
DJANGO_SECRET_KEY=gere-uma-chave-segura-aqui
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# ── Base de dados ────────────────────────────────────────────
# Opção 1 — SQLite (desenvolvimento, sem configuração adicional)
# (deixe DATABASE_URL e USE_POSTGRES em branco)

# Opção 2 — PostgreSQL via URL
# DATABASE_URL=postgres://user:password@localhost:5432/studies_db

# Opção 3 — PostgreSQL via variáveis separadas
# USE_POSTGRES=true
# POSTGRES_DB=studies_db
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=secret
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432

# ── Ollama ───────────────────────────────────────────────────
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_EMBED_MODEL=nomic-embed-text:latest
OLLAMA_CHAT_MODEL=gemma2:2b

# ── ChromaDB ─────────────────────────────────────────────────
CHROMA_PERSIST_DIR=chroma_data

# ── Celery / Redis ────────────────────────────────────────────
# CELERY_BROKER_URL=redis://127.0.0.1:6379/0
# (se omitido em DEBUG=true, Celery corre em modo eager — sem Redis)

# ── RAG (opcional) ───────────────────────────────────────────
RAG_TOP_K=5
RAG_CHUNK_SIZE=1500
RAG_CHUNK_OVERLAP=200
RAG_MAX_CONTEXT_CHARS=12000
```

> **Gerar uma chave secreta:**
> ```bash
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

### 3. Backend (Django)

```bash
cd backend

# Criar e activar ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Instalar dependências
pip install -r ../requirements.txt

# Aplicar migrações
python manage.py migrate

# (Opcional) Criar superutilizador para o admin
python manage.py createsuperuser

# Iniciar servidor de desenvolvimento
python manage.py runserver
```

O backend ficará disponível em `http://127.0.0.1:8000`.

### 4. Ollama (modelos de IA)

Instale o [Ollama](https://ollama.com/download) e faça pull dos modelos necessários:

```bash
# Modelo de embeddings (obrigatório)
ollama pull nomic-embed-text

# Modelo de chat (obrigatório — pode trocar por outro)
ollama pull gemma2:2b

# Alternativas para o modelo de chat
ollama pull llama3.2
ollama pull mistral
```

Verifique que o Ollama está em execução:
```bash
curl http://localhost:11434/api/tags
```

### 5. Frontend (Vue 3)

```bash
cd frontend

# Instalar dependências
npm install

# Iniciar servidor de desenvolvimento
npm run dev
```

O frontend ficará disponível em `http://localhost:5173`. O proxy do Vite redireciona `/api` para o backend automaticamente — os cookies HttpOnly funcionam sem configuração adicional.

### 6. Celery (processamento assíncrono)

Em **desenvolvimento**, se não tiver Redis, o processamento corre em modo *eager* (síncrono) automaticamente quando `DJANGO_DEBUG=true`.

Para usar Celery com Redis:
```bash
# Numa janela de terminal separada (dentro de backend/)
source .venv/bin/activate
celery -A studies_assistant worker --loglevel=info
```

---

## Executar em Desenvolvimento

Precisa de **três terminais** (ou dois se usar o modo eager):

```bash
# Terminal 1 — Backend Django
cd backend && python manage.py runserver

# Terminal 2 — Frontend Vite
cd frontend && npm run dev

# Terminal 3 — Celery Worker (opcional; necessário se CELERY_BROKER_URL estiver definido)
cd backend && celery -A studies_assistant worker --loglevel=info
```

Aceda à aplicação em **http://localhost:5173**.

O painel de administração Django está disponível em **http://127.0.0.1:8000/admin**.

---

## Estrutura do Projeto

```
studies-assistant/
├── .env                          # Variáveis de ambiente (não versionado)
├── requirements.txt              # Dependências Python
├── chroma_data/                  # Dados persistidos do ChromaDB (não versionado)
│
├── backend/
│   ├── manage.py
│   ├── studies_assistant/
│   │   ├── settings.py           # Configuração central do Django
│   │   ├── urls.py               # Roteamento principal
│   │   ├── celery.py             # Configuração do Celery
│   │   └── wsgi.py / asgi.py
│   │
│   ├── core/                     # App de autenticação e utilitários
│   │   ├── authentication.py     # JWT via cookie HttpOnly
│   │   ├── jwt_cookie_views.py   # Login, refresh, logout com cookies
│   │   ├── serializers.py        # Registo e perfil de utilizador
│   │   ├── pagination.py         # Paginação reutilizável
│   │   ├── throttles.py          # Rate limiting por IP
│   │   └── exception_handler.py  # Respostas de erro traduzidas
│   │
│   ├── documents/                # App de documentos e RAG
│   │   ├── models.py             # Modelo Document com estado de extração
│   │   ├── serializers.py        # Upload, detalhe, RAG ask/generate
│   │   ├── views.py              # Upload, listagem, RAG endpoints
│   │   ├── tasks.py              # Tarefa Celery de extração/indexação
│   │   ├── extraction.py         # Orquestração: texto → chunks → vetores → Chroma
│   │   ├── pdf_text.py           # Extração de texto com pypdf
│   │   ├── chunking.py           # Divisão em chunks com overlap
│   │   ├── ollama_embed.py       # Cliente HTTP para embeddings (Ollama)
│   │   ├── ollama_chat.py        # Cliente HTTP para chat completion (Ollama)
│   │   ├── chroma_index.py       # Upsert, delete e similarity search no ChromaDB
│   │   ├── rag.py                # Pipeline RAG completo
│   │   └── management/commands/
│   │       ├── chroma_inspect.py # Inspeciona vetores no ChromaDB
│   │       └── show_chunks.py    # Mostra chunks de um documento
│   │
│   └── chat/                     # App de conversas
│       ├── models.py             # Conversation e Message
│       ├── serializers.py        # Conversas, mensagens, envio com PDF
│       ├── views.py              # CRUD de conversas e envio de mensagens
│       └── pdf_attachment.py     # Extração de PDF anexado no chat
│
└── frontend/
    ├── vite.config.ts            # Proxy /api → backend
    ├── src/
    │   ├── main.ts               # Bootstrap da app
    │   ├── App.vue
    │   ├── router/               # Vue Router com guards de autenticação
    │   ├── composables/
    │   │   ├── useAuth.ts        # Estado de sessão global
    │   │   └── useTheme.ts       # Tema claro/escuro
    │   ├── lib/
    │   │   ├── api.ts            # fetch com refresh automático de JWT
    │   │   ├── markdown.ts       # Renderização Markdown segura
    │   │   └── paginatedList.ts  # Utilitário para percorrer paginação
    │   ├── components/
    │   │   ├── ConfirmDialog.vue
    │   │   └── ThemeToggle.vue
    │   ├── views/
    │   │   ├── LoginView.vue
    │   │   ├── RegisterView.vue
    │   │   ├── ChatView.vue        # Interface principal de chat
    │   │   ├── DocumentsView.vue   # Gestão de PDFs
    │   │   └── StudyMaterialsView.vue  # Geração de materiais
    │   └── assets/
    │       ├── base.css            # Design tokens e variáveis CSS
    │       └── ui.css              # Componentes de UI reutilizáveis
    └── ...
```

---

## Endpoints da API

Todos os endpoints são prefixados com `/api/`. A autenticação usa cookies HttpOnly — inclua `credentials: 'include'` nas chamadas fetch.

### Autenticação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/auth/register/` | Criar conta (`username`, `password`, `password_confirm`, `email?`) |
| `POST` | `/api/auth/login/` | Iniciar sessão (`username`, `password`) → define cookies |
| `GET`  | `/api/auth/me/` | Perfil do utilizador autenticado |
| `POST` | `/api/auth/token/refresh/` | Renovar access token (via cookie refresh) |
| `POST` | `/api/auth/logout/` | Terminar sessão (invalida refresh, limpa cookies) |
| `GET`  | `/api/health/` | Verificação de saúde do servidor |

### Documentos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/documents/upload/` | Upload de PDF (multipart/form-data, campo `file`) |
| `GET`  | `/api/documents/` | Listar documentos do utilizador (paginado) |
| `GET`  | `/api/documents/{id}/` | Detalhe e estado de processamento de um documento |
| `DELETE` | `/api/documents/{id}/` | Apagar documento (ficheiro + vetores Chroma) |

**Estados de extração** (`extraction_status`): `pending` → `processing` → `done` / `failed`

### RAG

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/rag/ask/` | Pergunta RAG (`question`, `document_ids?`) |
| `POST` | `/api/rag/generate/` | Gerar material (`kind`, `title?`, `topic?`, `instructions?`, `document_ids?`) |

**Tipos de material** (`kind`): `summary`, `exercise_list`, `roadmap`

### Chat

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET`  | `/api/chat/conversations/` | Listar conversas (paginado) |
| `POST` | `/api/chat/conversations/` | Criar nova conversa |
| `DELETE` | `/api/chat/conversations/{id}/` | Apagar conversa |
| `PATCH` | `/api/chat/conversations/{id}/` | Renomear conversa (`title`) |
| `GET`  | `/api/chat/conversations/{id}/messages/` | Listar mensagens (paginado) |
| `POST` | `/api/chat/conversations/{id}/messages/` | Enviar mensagem (`content`, `file?`, `document_ids?`) |

---

## Pipeline RAG

Quando um PDF é carregado, o seguinte pipeline corre em background (Celery):

```
1. Extração de texto     pypdf → texto bruto
2. Normalização          Remove ruído de PDF (espaços múltiplos, quebras excessivas)
3. Chunking              Janela deslizante com overlap (padrão: 1500 chars, overlap 200)
                         Snap inteligente em separadores naturais (parágrafo, frase, espaço)
4. Embeddings            Ollama /api/embed com nomic-embed-text em batches de 32
5. Indexação             ChromaDB upsert com metadados: document_id, user_id, chunk_index
```

Quando o utilizador envia uma pergunta:

```
1. Embedding da pergunta    Ollama /api/embed
2. Similarity search        ChromaDB query filtrado por user_id (e document_ids opcionais)
3. Diversificação           Limita chunks por documento (RAG_MAX_CHUNKS_PER_DOCUMENT)
4. Construção de contexto   Junta chunks até RAG_MAX_CONTEXT_CHARS
5. Geração                  Ollama /api/chat com system prompt + contexto + pergunta
6. Resposta                 Texto gerado + sources (document_id, chunk_index, excerpt)
```

---

## Variáveis de Ambiente — Referência Completa

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `DJANGO_SECRET_KEY` | — | **Obrigatório.** Chave secreta do Django |
| `DJANGO_DEBUG` | `false` | Modo debug (nunca `true` em produção) |
| `DJANGO_ALLOWED_HOSTS` | — | Hosts permitidos, separados por vírgula |
| `DATABASE_URL` | — | URL completa de PostgreSQL |
| `USE_POSTGRES` | `false` | Ativar PostgreSQL com variáveis `POSTGRES_*` |
| `POSTGRES_DB` | — | Nome da base de dados |
| `POSTGRES_USER` | `postgres` | Utilizador da base de dados |
| `POSTGRES_PASSWORD` | — | Password da base de dados |
| `POSTGRES_HOST` | `localhost` | Host do PostgreSQL |
| `POSTGRES_PORT` | `5432` | Porta do PostgreSQL |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | URL base do Ollama |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text:latest` | Modelo de embeddings |
| `OLLAMA_CHAT_MODEL` | `gemma2:2b` | Modelo de chat/geração |
| `OLLAMA_EMBED_TIMEOUT` | `120` | Timeout para embeddings (segundos) |
| `OLLAMA_CHAT_TIMEOUT` | `180` | Timeout para chat completion (segundos) |
| `OLLAMA_EMBED_BATCH_SIZE` | `32` | Chunks por request de embedding |
| `CHROMA_PERSIST_DIR` | `chroma_data` | Directório de persistência do ChromaDB |
| `CHROMA_COLLECTION_NAME` | `study_documents` | Nome da coleção no ChromaDB |
| `RAG_CHUNK_SIZE` | `1500` | Tamanho máximo de cada chunk (chars) |
| `RAG_CHUNK_OVERLAP` | `200` | Overlap entre chunks (chars) |
| `RAG_TOP_K` | `5` | Número de chunks recuperados por pesquisa |
| `RAG_MAX_CONTEXT_CHARS` | `12000` | Limite do contexto enviado ao LLM (chars) |
| `RAG_MAX_QUESTION_LENGTH` | `4000` | Limite da pergunta do utilizador (chars) |
| `RAG_DIVERSIFY_RESULTS` | `true` | Diversificar resultados entre documentos |
| `RAG_MAX_CHUNKS_PER_DOCUMENT` | `2` | Máximo de chunks por documento na diversificação |
| `RAG_MAX_CHAT_ATTACHMENT_CONTEXT_CHARS` | `8000` | Limite do contexto de PDF anexado no chat |
| `RAG_SYSTEM_PROMPT` | *(interno)* | System prompt personalizado para o LLM |
| `CELERY_BROKER_URL` | `redis://127.0.0.1:6379/0` | URL do Redis para Celery |
| `CELERY_TASK_ALWAYS_EAGER` | `false` | Forçar modo síncrono no Celery |
| `CHAT_MAX_CONVERSATIONS_PER_USER` | `500` | Limite de conversas por utilizador (0 = ilimitado) |
| `RAG_THROTTLE_RATE` | `30/min` | Rate limit para endpoints RAG |
| `CHAT_THROTTLE_RATE` | `60/min` | Rate limit para endpoints de chat |
| `AUTH_LOGIN_THROTTLE_RATE` | `5/min` | Rate limit para login (por IP) |
| `AUTH_REGISTER_THROTTLE_RATE` | `3/min` | Rate limit para registo (por IP) |
| `JWT_COOKIE_SAMESITE` | *(auto)* | `Lax` em dev, `None` em produção HTTPS |
| `JWT_COOKIE_SECURE` | *(auto)* | `false` em DEBUG, `true` em produção |
| `DJANGO_CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Origens CORS permitidas |

---

## Comandos de Gestão Úteis

```bash
# Inspecionar vetores no ChromaDB
python manage.py chroma_inspect

# Inspecionar vetores de um documento específico
python manage.py chroma_inspect --document 5

# Ver chunks recalculados de um documento
python manage.py show_chunks 3

# Listar todos os documentos na base de dados
python manage.py show_chunks --list

# Ver embeddings gerados para um documento
python manage.py show_embeddings 5

# Testar apenas os primeiros 3 chunks
python manage.py show_embeddings 5 --limit 3
```

---

## Deploy em Produção

### Requisitos mínimos

- Servidor com Python 3.11+, Redis e PostgreSQL
- Ollama acessível pelo backend (pode ser local ou servidor dedicado)
- Reverse proxy (nginx ou Caddy) com HTTPS

### Checklist de produção

```bash
# 1. Variáveis obrigatórias
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<chave-longa-e-aleatória>
DJANGO_ALLOWED_HOSTS=meudominio.com
DATABASE_URL=postgres://...
DJANGO_CORS_ALLOWED_ORIGINS=https://meudominio.com

# 2. Cookies seguros (HTTPS)
JWT_COOKIE_SAMESITE=None
JWT_COOKIE_SECURE=true

# 3. Ficheiros estáticos
python manage.py collectstatic --no-input

# 4. Base de dados
python manage.py migrate

# 5. Gunicorn (backend)
gunicorn studies_assistant.wsgi:application --workers 4 --bind 0.0.0.0:8000

# 6. Celery Worker
celery -A studies_assistant worker --loglevel=warning --concurrency 2
```

### Build do frontend

```bash
cd frontend
npm run build
# Ficheiros gerados em frontend/dist/ — servir como ficheiros estáticos via nginx
```

### Exemplo de configuração nginx

```nginx
server {
    listen 443 ssl;
    server_name meudominio.com;

    # Ficheiros estáticos do frontend
    root /var/www/studies/frontend/dist;
    index index.html;

    # SPA — todas as rotas para index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy para o backend Django
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 30M;
    }

    # Ficheiros media (PDFs)
    location /media/ {
        alias /var/www/studies/backend/media/;
    }
}
```

---

## Contribuições

Contribuições são bem-vindas! Por favor:

1. Faça fork do repositório
2. Crie uma branch: `git checkout -b feature/minha-funcionalidade`
3. Commit com mensagem clara: `git commit -m "feat: descrição da funcionalidade"`
4. Push: `git push origin feature/minha-funcionalidade`
5. Abra um Pull Request

---

