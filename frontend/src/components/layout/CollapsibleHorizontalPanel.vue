<script setup lang="ts">
/**
 * CollapsibleHorizontalPanel.vue
 * Ported from: planning/UI/src/components/CollapsibleHorizontalPanel.tsx
 * 
 * Collapsible side panel with vertical label when collapsed.
 */
import ResizablePanel from './ResizablePanel.vue'

interface Props {
  isCollapsed: boolean
  side: 'left' | 'right'
  defaultWidth?: number
  minWidth?: number
  maxWidth?: number
  label: string
}

const _props = withDefaults(defineProps<Props>(), {
  defaultWidth: 320,
  minWidth: 280,
  maxWidth: 600,
})
void _props

const emit = defineEmits<{
  toggle: []
}>()
</script>

<template>
  <!-- Collapsed state -->
  <div
    v-if="isCollapsed"
    class="w-8 bg-slate-50 border-slate-200 flex-shrink-0"
    :class="side === 'left' ? 'border-r' : 'border-l'"
  >
    <button
      @click="emit('toggle')"
      class="h-full w-full hover:bg-slate-100 transition-colors flex items-center justify-center"
    >
      <span
        class="text-xs font-medium text-slate-600 whitespace-nowrap"
        style="writing-mode: vertical-rl; transform: rotate(180deg)"
      >
        {{ label }}
      </span>
    </button>
  </div>

  <!-- Expanded state -->
  <ResizablePanel
    v-else
    :side="side"
    :default-width="defaultWidth"
    :min-width="280"
    :max-width="600"
  >
    <slot />
  </ResizablePanel>
</template>
