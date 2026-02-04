<script setup lang="ts">
/**
 * ConnectionLine.vue
 * Ported from: planning/UI/src/components/ConnectionLine.tsx
 * 
 * SVG bezier curves connecting workflow nodes.
 * Adapted for Vue Flow Custom Edge.
 */
import { computed } from 'vue'
import { type EdgeProps, BaseEdge, getBezierPath } from '@vue-flow/core'

const props = defineProps<EdgeProps>()

const emit = defineEmits<{
  delete: [connectionId: string]
}>()

// Use Vue Flow's getBezierPath for standard behavior, or keep custom logic if preferred.
// The original used a custom adaptive offset. Let's try to keep the custom feel but using the correct props.
// However, getBezierPath is very robust. Let's see if we can just use our custom path logic with the new props.

const pathD = computed(() => {
  const distX = props.targetX - props.sourceX
  // Adaptive offset prevents huge loops when nodes are close
  const controlPointOffset = Math.max(Math.min(distX / 2, 100), 20) 
  
  return `M ${props.sourceX} ${props.sourceY} C ${props.sourceX + controlPointOffset} ${props.sourceY}, ${props.targetX - controlPointOffset} ${props.targetY}, ${props.targetX} ${props.targetY}`
})
</script>

<template>
  <g class="group cursor-pointer pointer-events-auto">
    <!-- Base interaction path -->
    <path
      :d="pathD"
      stroke="transparent"
      stroke-width="20"
      fill="none"
      @click="emit('delete', id)"
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
    <g class="opacity-0 group-hover:opacity-100 transition-opacity" @click="emit('delete', id)">
      <circle
        :cx="(sourceX + targetX) / 2"
        :cy="(sourceY + targetY) / 2"
        r="8"
        fill="white"
        stroke="#ef4444"
        stroke-width="2"
      />
      <text
        :x="(sourceX + targetX) / 2"
        :y="(sourceY + targetY) / 2 + 4"
        text-anchor="middle"
        font-size="12"
        fill="#ef4444"
        class="pointer-events-none"
      >
        ×
      </text>
    </g>
  </g>
</template>
