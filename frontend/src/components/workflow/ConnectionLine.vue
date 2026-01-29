<script setup lang="ts">
/**
 * ConnectionLine.vue
 * Ported from: planning/UI/src/components/ConnectionLine.tsx
 * 
 * SVG bezier curves connecting workflow nodes.
 */

interface Props {
  id: string
  sourceNode: any
  targetNode: any
  sourcePortIndex: number
  targetPortIndex: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  delete: [connectionId: string]
}>()

// Calculate connection path
const startX = (props.sourceNode.position?.x ?? props.sourceNode.x) + 280    // Node width
const startY = (props.sourceNode.position?.y ?? props.sourceNode.y) + 70 + props.sourcePortIndex * 28
const endX = (props.targetNode.position?.x ?? props.targetNode.x)
const endY = (props.targetNode.position?.y ?? props.targetNode.y) + 70 + props.targetPortIndex * 28

const pathD = `M ${startX} ${startY} C ${startX + 100} ${startY}, ${endX - 100} ${endY}, ${endX} ${endY}`
</script>

<template>
  <g class="group cursor-pointer" @click="emit('delete', id)">
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
