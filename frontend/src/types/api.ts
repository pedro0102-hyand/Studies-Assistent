export interface RagSource {
  document_id: number
  chunk_index: number
  original_name: string
  excerpt: string
}

export interface ApiDocument {
  id: number
  original_name: string
  file_url?: string
  text_char_count?: number
  chunk_count?: number
  embedded_chunk_count?: number
  embedding_error?: string
  chroma_indexed_at?: string | null
  chroma_error?: string
  extraction_error?: string
  extraction_status?: 'pending' | 'processing' | 'done' | 'failed'
  created_at?: string
  updated_at?: string
}

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
  sources: RagSource[]
  created_at: string
}

export type MaterialKind = 'summary' | 'exercise_list' | 'roadmap'

export interface GenerateResponse {
  kind: MaterialKind
  title: string
  markdown: string
  sources?: RagSource[]
}
