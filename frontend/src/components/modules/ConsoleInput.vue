<script setup lang="ts">
import { ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { Send } from 'lucide-vue-next'
import { useConsoleStore } from '../../stores/console'
import { useWorkflowStore } from '../../stores/workflow'

const consoleStore = useConsoleStore()
const workflowStore = useWorkflowStore()
const { input } = storeToRefs(consoleStore)
const selectedAgent = ref<string>('system')

const agents = [
  { value: 'system', label: 'System' },
  { value: 'scholar', label: 'Scholar' },
  { value: 'engineer', label: 'Engineer' },
  { value: 'reviewer', label: 'Reviewer' }
]

function handleSend() {
  if (!input.value.trim()) return

  consoleStore.sendMessage(input.value, selectedAgent.value)
  input.value = ''
  
  // Ensure console is expanded when sending
  if (workflowStore.isConsoleCollapsed) {
    workflowStore.toggleConsole()
  }
}

// Auto-expand console when user starts typing
watch(input, (newVal) => {
  if (newVal && workflowStore.isConsoleCollapsed) {
    workflowStore.toggleConsole()
  }
})
</script>

<template>
  <div class="border-t border-slate-200 p-3 bg-white">
    <div class="flex gap-2">
      <select
        v-model="selectedAgent"
        class="px-2 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
      >
        <option v-for="agent in agents" :key="agent.value" :value="agent.value">
          {{ agent.label }}
        </option>
      </select>
      
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
</template>
