<script setup lang="ts">
/**
 * ConsoleModule.vue
 * Ported from: planning/UI/src/components/ConsoleModule.tsx
 * 
 * Real-time log viewer with agent chat interface.
 */
import { ref, nextTick, onMounted, watch } from 'vue'
import { Terminal, User, Bot } from 'lucide-vue-next'
import { useConsoleStore } from '../../stores/console'
import { storeToRefs } from 'pinia'

const store = useConsoleStore()
const { messages } = storeToRefs(store)
const messagesEndRef = ref<HTMLDivElement | null>(null)

function scrollToBottom() {
  nextTick(() => {
    messagesEndRef.value?.scrollIntoView({ behavior: 'smooth' })
  })
}

// Watch for new messages to scroll to bottom
watch(() => messages.value.length, () => {
  scrollToBottom()
})

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
  </div>
</template>
