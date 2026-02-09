<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
// @ts-ignore
import DOMPurify from 'dompurify'

const props = defineProps<{
  content: string
}>()

const md = new MarkdownIt({
  html: true,
  breaks: true,
  linkify: true
})

const isJson = computed(() => {
  if (!props.content) return false
  try {
    const trimmed = props.content.trim()
    if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
        JSON.parse(trimmed)
        return true
    }
    return false
  } catch (e) {
    return false
  }
})

const formattedJson = computed(() => {
  if (!isJson.value) return ''
  try {
    const obj = JSON.parse(props.content)
    return JSON.stringify(obj, null, 2)
  } catch (e) {
    return props.content
  }
})

const renderedMarkdown = computed(() => {
  if (isJson.value) return ''
  // Use markdown-it to render
  const rawHtml = md.render(props.content)
  // Sanitize
  return DOMPurify.sanitize(rawHtml)
})
</script>

<template>
  <div class="smart-renderer text-xs font-mono leading-relaxed w-full min-w-0">
    <!-- JSON View -->
    <div v-if="isJson" class="bg-gray-50/50 p-2 rounded border border-gray-200 w-full">
      <pre class="whitespace-pre-wrap break-all text-xs font-mono text-slate-700 w-full overflow-hidden">{{ formattedJson }}</pre>
    </div>
    
    <!-- Markdown View -->
    <div v-else class="markdown-body" v-html="renderedMarkdown"></div>
  </div>
</template>

<style>
/* Scoped styles for markdown content to match console aesthetic */
.smart-renderer .markdown-body > *:first-child {
  margin-top: 0;
}
.smart-renderer .markdown-body > *:last-child {
  margin-bottom: 0;
}

.smart-renderer .markdown-body p {
  margin-bottom: 0.5em;
  white-space: pre-wrap; /* Preserve whitespace in text */
}

.smart-renderer .markdown-body h1,
.smart-renderer .markdown-body h2,
.smart-renderer .markdown-body h3,
.smart-renderer .markdown-body h4 {
  font-weight: 600;
  margin-top: 1em;
  margin-bottom: 0.5em;
  color: #1e293b; /* slate-800 */
}

.smart-renderer .markdown-body ul,
.smart-renderer .markdown-body ol {
  padding-left: 1.5em;
  margin-bottom: 0.5em;
  list-style-type: disc;
}

.smart-renderer .markdown-body li {
  margin-bottom: 0.25em;
}

.smart-renderer .markdown-body strong {
  font-weight: 600;
  color: #0f172a; /* slate-900 */
}

.smart-renderer .markdown-body code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  background-color: #f1f5f9; /* slate-100 */
  padding: 0.1em 0.3em;
  border-radius: 0.2em;
  color: #0f172a;
  font-size: 0.9em;
}

.smart-renderer .markdown-body pre {
  background-color: #f8fafc; /* slate-50 */
  padding: 0.75em;
  border-radius: 0.375em;
  border: 1px solid #e2e8f0; /* slate-200 */
  margin-bottom: 0.75em;
  /* Force wrapping to prevent overflow */
  white-space: pre-wrap;
  word-wrap: break-word; /* IE fallback */
  overflow-wrap: break-word;
  word-break: break-all;
  max-width: 100%;
  overflow-x: hidden; /* Hide scrollbar since we wrap */
}

.smart-renderer .markdown-body pre code {
  background-color: transparent;
  padding: 0;
  border-radius: 0;
  color: inherit;
  font-size: inherit;
}

.smart-renderer .markdown-body a {
  color: #2563eb; /* blue-600 */
  text-decoration: underline;
}

.smart-renderer .markdown-body blockquote {
  border-left: 3px solid #cbd5e1; /* slate-300 */
  padding-left: 1em;
  color: #64748b; /* slate-500 */
  margin-bottom: 0.75em;
  font-style: italic;
}
</style>
