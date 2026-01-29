<script setup lang="ts">
/**
 * ResizablePanel.vue
 * Ported from: planning/UI/src/components/ResizablePanel.tsx
 * 
 * Supports both horizontal (side bar) and vertical (stacked panels) resizing.
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'

interface Props {
  // Horizontal mode props
  side?: 'left' | 'right'
  defaultWidth?: number
  minWidth?: number
  maxWidth?: number
  
  // Vertical mode props
  orientation?: 'horizontal' | 'vertical'
  defaultHeight?: number
  minHeight?: number
  maxHeight?: number
  
  // Common
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  side: 'left',
  defaultWidth: 320,
  minWidth: 280,
  maxWidth: 600,
  orientation: 'horizontal',
  defaultHeight: 300,
  minHeight: 100,
  maxHeight: 800,
})

const size = ref(props.orientation === 'horizontal' ? props.defaultWidth : props.defaultHeight)
const isResizing = ref(false)
const startPos = ref(0)
const startSize = ref(0)

const panelStyle = computed(() => {
  if (props.orientation === 'horizontal') {
    return {
      width: `${size.value}px`,
      flexShrink: 0,
      height: '100%'
    }
  } else {
    return {
      height: `${size.value}px`,
      flexShrink: 0,
      width: '100%'
    }
  }
})

function handleMouseDown(e: MouseEvent) {
  e.preventDefault()
  isResizing.value = true
  startPos.value = props.orientation === 'horizontal' ? e.clientX : e.clientY
  startSize.value = size.value
  
  document.body.style.cursor = props.orientation === 'horizontal' ? 'ew-resize' : 'ns-resize'
  document.body.style.userSelect = 'none'
}

function handleMouseMove(e: MouseEvent) {
  if (!isResizing.value) return
  
  const currentPos = props.orientation === 'horizontal' ? e.clientX : e.clientY
  let delta = currentPos - startPos.value
  
  // Invert delta if resizing from right side (for horizontal)
  if (props.orientation === 'horizontal' && props.side === 'right') {
    delta = -delta
  } 
  // For vertical, we assume resizing from bottom (standard flow), so positive delta increases height
  
  const newSize = startSize.value + delta
  
  if (props.orientation === 'horizontal') {
    size.value = Math.min(Math.max(newSize, props.minWidth), props.maxWidth)
  } else {
    size.value = Math.min(Math.max(newSize, props.minHeight), props.maxHeight)
  }
}

function handleMouseUp() {
  if (isResizing.value) {
    isResizing.value = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }
}

onMounted(() => {
  window.addEventListener('mousemove', handleMouseMove)
  window.addEventListener('mouseup', handleMouseUp)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', handleMouseMove)
  window.removeEventListener('mouseup', handleMouseUp)
})
</script>

<template>
  <div class="relative flex flex-col bg-white border-slate-200" :style="panelStyle" :class="[
    orientation === 'horizontal' ? (side === 'left' ? 'border-r' : 'border-l') : 'border-b'
  ]">
    <!-- Optional Title Header -->
    <div v-if="title" class="px-3 py-2 border-b border-slate-200 font-medium text-sm text-slate-700 bg-white">
      {{ title }}
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-auto relative">
      <slot />
    </div>

    <!-- Horizontal Resize Handle -->
    <div
      v-if="orientation === 'horizontal'"
      :class="[
        'absolute top-0 bottom-0 w-1 cursor-ew-resize hover:bg-blue-500 transition-colors z-20',
        side === 'left' ? 'right-0' : 'left-0'
      ]"
      @mousedown="handleMouseDown"
    />

    <!-- Vertical Resize Handle -->
    <div
      v-if="orientation === 'vertical'"
      class="absolute bottom-0 left-0 right-0 h-1 cursor-ns-resize hover:bg-blue-500 transition-colors z-20"
      @mousedown="handleMouseDown"
    />
  </div>
</template>
