<script setup lang="ts">
/**
 * ConsoleModule.vue
 * Ported from: planning/UI/src/components/ConsoleModule.tsx
 * 
 * Real-time log viewer with agent chat interface.
 */
import { ref, nextTick, onMounted, watch } from 'vue'
import { User, Bot } from 'lucide-vue-next'
import { useConsoleStore } from '../../stores/console'
import { storeToRefs } from 'pinia'
import SmartMessageRenderer from '../common/SmartMessageRenderer.vue'

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


    <!-- Messages -->
    <div class="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-xs">
      <div v-for="message in messages" :key="message.id" class="flex gap-3">
        <span class="text-slate-400 whitespace-nowrap">
          {{ formatTime(message.timestamp) }}
        </span>
        <div class="flex-1 min-w-0"> <!-- Added flex-1 and min-w-0 to prevent overflow -->
          <!-- User message -->
          <div v-if="message.type === 'user'" class="flex items-start gap-2">
            <User class="w-4 h-4 text-slate-600 mt-0.5 flex-shrink-0" />
            <span class="text-slate-900 break-words">{{ message.content }}</span>
          </div>
          
          <!-- Agent message -->
          <div v-else-if="message.type === 'agent'" class="flex items-start gap-2">
            <Bot :class="['w-4 h-4 mt-0.5 flex-shrink-0', getAgentColor(message.agent)]" />
            <div class="flex-1 min-w-0">
              <span :class="['font-semibold block mb-1', getAgentColor(message.agent)]">
                {{ getAgentName(message.agent) }}:
              </span>
              <!-- Use SmartMessageRenderer for agent messages -->
              <SmartMessageRenderer :content="message.content" />
            </div>
          </div>
          
          <!-- System message -->
          <span v-else class="text-slate-500 italic break-words">{{ message.content }}</span>
        </div>
      </div>
      <div ref="messagesEndRef" />
    </div>
  </div>
</template>
