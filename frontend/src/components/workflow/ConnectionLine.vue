<script setup lang="ts">
/**
 * ConnectionLine.vue
 * Ported from: planning/UI/src/components/ConnectionLine.tsx
 * 
 * SVG bezier curves connecting workflow nodes.
 */

interface Props {
  id: string
  startX: number
  startY: number
  endX: number
  endY: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  delete: [connectionId: string]
}>()

// Calculate connection path directly from props
// Use adaptive control points to avoid crossing when nodes are close
const distX = props.endX - props.startX
const controlPointOffset = Math.max(Math.min(distX / 2, 100), 20) 

const pathD = `M ${props.startX} ${props.startY} C ${props.startX + controlPointOffset} ${props.startY}, ${props.endX - controlPointOffset} ${props.endY}, ${props.endX} ${props.endY}`
</script>

<template>
  <g class="group cursor-pointer pointer-events-auto" @click="emit('delete', id)">
    <!-- Invisible wider path for easier click detection -->
    <path
      :d="pathD"
      stroke="transparent"
      stroke-width="12"
      fill="none"
    />
    
    <!-- Visible connection line -->
    <path
      :d="pathD"
      stroke="#94a3b8"
      stroke-width="2"
      fill="none"
      class="group-hover:stroke-red-400 transition-colors"
    />
    
    <!-- Delete indicator on hover -->
    <circle
      :cx="(startX + endX) / 2"
      :cy="(startY + endY) / 2"
      r="8"
      fill="white"
      stroke="#ef4444"
      stroke-width="2"
      class="opacity-0 group-hover:opacity-100 transition-opacity"
    />
    <text
      :x="(startX + endX) / 2"
      :y="(startY + endY) / 2 + 4"
      text-anchor="middle"
      font-size="12"
      fill="#ef4444"
      class="opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"
    >
      ×
    </text>
  </g>
</template>
