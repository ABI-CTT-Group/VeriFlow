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
    const rawObj = JSON.parse(props.content)
    
    // Check if we have a wrapped log with 'final_output' (e.g. Engineer Logs)
    // If so, we only want to render the final_output content.
    let targetObj = rawObj
    if (rawObj.final_output && typeof rawObj.final_output === 'object') {
        targetObj = rawObj.final_output
    }

    // --- SMART RENDERING LOGIC ---
    // Check if this looks like an Engineer Agent Output (contains Dockerfile or CWL)
    const keys = Object.keys(targetObj)
    const hasCodeArtifacts = keys.some(k => 
      k === 'Dockerfile' || k.endsWith('.cwl') || k.endsWith('.py') || k === 'infrastructure_code' || k === 'generated_code'
    )

    if (hasCodeArtifacts) {
      let markdownOutput = ''

      // 1. Dockerfile
      if (targetObj.Dockerfile) {
        markdownOutput += `### Dockerfile\n\`\`\`dockerfile\n${targetObj.Dockerfile}\n\`\`\`\n\n`
      }

      // 2. Iterate other keys (CWL, Python, etc.)
      keys.forEach(key => {
        if (key === 'Dockerfile') return // Already handled
        
        const value = targetObj[key]
        if (typeof value === 'string') {
           if (key.endsWith('.cwl')) {
             markdownOutput += `### ${key}\n\`\`\`yaml\n${value}\n\`\`\`\n\n`
           } else if (key.endsWith('.py')) {
             markdownOutput += `### ${key}\n\`\`\`python\n${value}\n\`\`\`\n\n`
           } else if (key !== 'thought_process') {
             // For other string keys, just print them if they are long/code-like, else json
             markdownOutput += `**${key}**:\n${value}\n\n`
           }
        } else {
           // nested objects or arrays
           markdownOutput += `**${key}**:\n\`\`\`json\n${JSON.stringify(value, null, 2)}\n\`\`\`\n\n`
        }
      })
      
      return markdownOutput
    }
    
    // Default JSON formatting
    return JSON.stringify(rawObj, null, 2)
  } catch (e) {
    // --- STREAMING / BROKEN JSON FALLBACK ---
    // If JSON.parse fails (likely due to streaming), try to extract known artifacts via manual tokenization
    // Simple regex is not enough because the closing quote might not exist yet.
    
    let markdownOutput = ''
    let foundArtifact = false

    const extractPartialContent = (text: string, keyName: string): string | null => {
        // pattern to find "key": "
        const keyPattern = `"${keyName}"\\s*:\\s*"`
        const regex = new RegExp(keyPattern)
        const match = text.match(regex)
        
        if (!match || match.index === undefined) return null

        const startIndex = match.index + match[0].length
        let content = ''
        let isEscaped = false
        
        // Scan character by character from start of value
        for (let i = startIndex; i < text.length; i++) {
            const char = text[i]
            
            if (isEscaped) {
                // Handle escape sequences
                if (char === 'n') content += '\n'
                else if (char === 'r') content += '\r'
                else if (char === 't') content += '\t'
                else if (char === '"') content += '"'
                else if (char === '\\') content += '\\'
                else content += char // Unknown escape, just keep char
                
                isEscaped = false
            } else {
                if (char === '\\') {
                    isEscaped = true
                } else if (char === '"') {
                    // Start of value is ", so unescaped " means END of string
                    // We stopped!
                    break 
                } else {
                    content += char
                }
            }
        }
        return content
    }

    // 1. Extract Dockerfile
    const dockerContent = extractPartialContent(props.content, 'Dockerfile')
    if (dockerContent && dockerContent.length > 5) { // Threshold to avoid false positives or empty
        markdownOutput += `### Dockerfile\n\`\`\`dockerfile\n${dockerContent}\n\`\`\`\n\n`
        foundArtifact = true
    }

    // 2. Extract CWL files (we need to find keys ending in .cwl)
    // Since we can't iterate keys in broken JSON, we'll scan for specific patterns
    // We assume the keys are explicitly ".cwl"
    // Regex to find all keys matching *.cwl
    const cwlKeyRegex = /"([^"]+\.cwl)"\s*:\s*"/g
    let cwlKeyMatch
    while ((cwlKeyMatch = cwlKeyRegex.exec(props.content)) !== null) {
        const filename = cwlKeyMatch[1]
        // Use our robust extractor for this specific filename
        const content = extractPartialContent(props.content, filename)
        if (content) {
             markdownOutput += `### ${filename}\n\`\`\`yaml\n${content}\n\`\`\`\n\n`
             foundArtifact = true
        }
    }

    if (foundArtifact) {
        return markdownOutput
    }
    
    return props.content
  }
})

const renderedMarkdown = computed(() => {
  // If we detected it as JSON and converted it to Markdown (Smart Rendering), render that.
  if (isJson.value) {
     // Check if our 'formattedJson' is actually Markdown (starts with # or ```)
     if (formattedJson.value.includes('```') || formattedJson.value.startsWith('###')) {
         return DOMPurify.sanitize(md.render(formattedJson.value))
     }
     return '' // Let the template handle it as <pre>
  }

  // --- NON-JSON CONTENT: Check for streaming Engineer output ---
  // Try to extract Dockerfile / CWL from streaming content
  const extractPartialContent = (text: string, keyName: string): string | null => {
      // pattern to find "key": "
      const keyPattern = `"${keyName}"\\s*:\\s*"`
      const regex = new RegExp(keyPattern)
      const match = text.match(regex)
      
      if (!match || match.index === undefined) return null

      const startIndex = match.index + match[0].length
      let content = ''
      let isEscaped = false
      
      // Scan character by character from start of value
      for (let i = startIndex; i < text.length; i++) {
          const char = text[i]
          
          if (isEscaped) {
              // Handle escape sequences
              if (char === 'n') content += '\n'
              else if (char === 'r') content += '\r'
              else if (char === 't') content += '\t'
              else if (char === '"') content += '"'
              else if (char === '\\') content += '\\'
              else content += char // Unknown escape, just keep char
              
              isEscaped = false
          } else {
              if (char === '\\') {
                  isEscaped = true
              } else if (char === '"') {
                  // Unescaped " means END of string value
                  break 
              } else {
                  content += char
              }
          }
      }
      return content
  }

  let markdownOutput = ''
  let foundArtifact = false

  // 1. Extract Dockerfile
  const dockerContent = extractPartialContent(props.content, 'Dockerfile')
  if (dockerContent && dockerContent.length > 5) {
      markdownOutput += `### Dockerfile\n\`\`\`dockerfile\n${dockerContent}\n\`\`\`\n\n`
      foundArtifact = true
  }

  // 2. Extract CWL files
  const cwlKeyRegex = /"([^"]+\.cwl)"\s*:\s*"/g
  let cwlKeyMatch
  while ((cwlKeyMatch = cwlKeyRegex.exec(props.content)) !== null) {
      const filename = cwlKeyMatch[1]
      const content = extractPartialContent(props.content, filename)
      if (content && content.length > 5) {
           markdownOutput += `### ${filename}\n\`\`\`yaml\n${content}\n\`\`\`\n\n`
           foundArtifact = true
      }
  }

  if (foundArtifact) {
      return DOMPurify.sanitize(md.render(markdownOutput))
  }

  // Standard Markdown (non-JSON, non-streaming input)
  const rawHtml = md.render(props.content)
  return DOMPurify.sanitize(rawHtml)
})


</script>

<template>
  <div class="smart-renderer text-xs font-mono leading-relaxed w-full min-w-0">
    <!-- JSON View (Only if simple JSON and not smart-rendered to Markdown) -->
    <div v-if="isJson && !renderedMarkdown" class="bg-gray-50/50 p-2 rounded border border-gray-200 w-full">
      <pre class="whitespace-pre-wrap break-all text-xs font-mono text-slate-700 w-full overflow-hidden">{{ formattedJson }}</pre>
    </div>
    
    <!-- Markdown View (Regular Markdown OR Smart-Rendered JSON) -->
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
