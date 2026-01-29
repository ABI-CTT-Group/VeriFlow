<script setup lang="ts">
/**
 * ConsoleModule.vue
 * Ported from: planning/UI/src/components/ConsoleModule.tsx
 * 
 * Real-time log viewer with agent chat interface.
 */
import { ref, nextTick, onMounted } from 'vue'
import { Send, Terminal, User, Bot } from 'lucide-vue-next'

interface Message {
  id: string
  type: 'user' | 'agent' | 'system'
  agent?: 'scholar' | 'engineer' | 'reviewer'
  content: string
  timestamp: Date
}

const messagesEndRef = ref<HTMLDivElement | null>(null)
const input = ref('')

const messages = ref<Message[]>([
  {
    id: '1',
    type: 'system',
    content: 'VeriFlow initialized. Agents ready.',
    timestamp: new Date(Date.now() - 300000)
  },
  {
    id: '2',
    type: 'agent',
    agent: 'scholar',
    content: 'Analyzing PDF: breast_cancer_segmentation.pdf...',
    timestamp: new Date(Date.now() - 240000)
  },
  {
    id: '3',
    type: 'agent',
    agent: 'scholar',
    content: 'Extracted ISA hierarchy: 1 Investigation, 1 Study, 2 Assays. Creating SDS metadata...',
    timestamp: new Date(Date.now() - 180000)
  },
  {
    id: '4',
    type: 'agent',
    agent: 'scholar',
    content: 'Identified measurements: DCE-MRI Scans (384 subjects), Tools: nnU-Net, Models: Pretrained weights',
    timestamp: new Date(Date.now() - 120000)
  },
  {
    id: '5',
    type: 'agent',
    agent: 'reviewer',
    content: 'Validation complete. Study design populated. Ready for workflow assembly.',
    timestamp: new Date(Date.now() - 60000)
  }
])

function scrollToBottom() {
  nextTick(() => {
    messagesEndRef.value?.scrollIntoView({ behavior: 'smooth' })
  })
}

function handleSend() {
  if (!input.value.trim()) return

  const newMessage: Message = {
    id: Date.now().toString(),
    type: 'user',
    content: input.value,
    timestamp: new Date()
  }

  messages.value.push(newMessage)
  input.value = ''
  scrollToBottom()

  // Simulate agent response
  setTimeout(() => {
    const response: Message = {
      id: (Date.now() + 1).toString(),
      type: 'agent',
      agent: 'reviewer',
      content: 'I understand your request. Processing...',
      timestamp: new Date()
    }
    messages.value.push(response)
    scrollToBottom()
  }, 1000)
}

function getAgentColor(agent?: string): string {
  switch (agent) {
    case 'scholar':
      return 'text-blue-600'
    case 'engineer':
      return 'text-purple-600'
    case 'reviewer':
      return 'text-green-600'
    default:
      return 'text-slate-600'
  }
}

function getAgentName(agent?: string): string {
  switch (agent) {
    case 'scholar':
      return 'Scholar Agent'
    case 'engineer':
      return 'Engineer Agent'
    case 'reviewer':
      return 'Reviewer Agent'
    default:
      return 'System'
  }
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(() => {
  scrollToBottom()
})
</script>

<template>
  <div class="h-full flex flex-col overflow-hidden">
    <!-- Header -->
    <div class="px-4 py-2 border-b border-slate-200 flex items-center justify-between bg-slate-50 flex-shrink-0">
      <div class="flex items-center gap-2">
        <Terminal class="w-4 h-4 text-slate-600" />
      </div>
      <div class="flex items-center gap-2">
        <div class="flex items-center gap-1">
          <div class="w-2 h-2 rounded-full bg-green-500"></div>
          <span class="text-xs text-slate-500">All agents active</span>
        </div>
      </div>
    </div>

    <!-- Messages -->
    <div class="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-xs">
      <div v-for="message in messages" :key="message.id" class="flex gap-3">
        <span class="text-slate-400 whitespace-nowrap">
          {{ formatTime(message.timestamp) }}
        </span>
        <div class="flex-1">
          <!-- User message -->
          <div v-if="message.type === 'user'" class="flex items-start gap-2">
            <User class="w-4 h-4 text-slate-600 mt-0.5" />
            <span class="text-slate-900">{{ message.content }}</span>
          </div>
          
          <!-- Agent message -->
          <div v-else-if="message.type === 'agent'" class="flex items-start gap-2">
            <Bot :class="['w-4 h-4 mt-0.5', getAgentColor(message.agent)]" />
            <div>
              <span :class="['font-semibold', getAgentColor(message.agent)]">
                {{ getAgentName(message.agent) }}:
              </span>
              {{ ' ' }}
              <span class="text-slate-700">{{ message.content }}</span>
            </div>
          </div>
          
          <!-- System message -->
          <span v-else class="text-slate-500 italic">{{ message.content }}</span>
        </div>
      </div>
      <div ref="messagesEndRef" />
    </div>

    <!-- Input - Fixed at bottom -->
    <div class="border-t border-slate-200 p-3 flex-shrink-0">
      <div class="flex gap-2">
        <input
          type="text"
          v-model="input"
          @keypress.enter="handleSend"
          placeholder="Chat with VeriFlow agents..."
          class="flex-1 px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          @click="handleSend"
          class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          <Send class="w-4 h-4" />
        </button>
      </div>
    </div>
  </div>
</template>
