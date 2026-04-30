import DOMPurify from 'dompurify'
import { marked } from 'marked'

marked.setOptions({
  gfm: true,
  breaks: true,
})

export function renderMarkdownToSafeHtml(markdown: string): string {
  const raw = marked.parse(markdown ?? '') as string
  return DOMPurify.sanitize(raw, {
    USE_PROFILES: { html: true },
  })
}

