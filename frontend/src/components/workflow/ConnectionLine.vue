<script setup lang="ts">
/**
 * ConnectionLine.vue
 * Ported from: planning/UI/src/components/ConnectionLine.tsx
 * 
 * SVG bezier curves connecting workflow nodes.
 * Adapted for Vue Flow Custom Edge.
 */
import { computed } from 'vue'
import { type EdgeProps } from '@vue-flow/core'

const props = defineProps<EdgeProps>()

const emit = defineEmits<{
  delete: [connectionId: string]
}>()

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
      :class="[
        'transition-colors',
        props.animated ? 'running-edge' : 'group-hover:stroke-red-400'
      ]"
    />
    
    <!-- Delete indicator on hover (only if not running) -->
    <g v-if="!props.animated" class="opacity-0 group-hover:opacity-100 transition-opacity" @click="emit('delete', id)">
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

<style scoped>
.running-edge {
  stroke: #3b82f6; /* Blue-500 */
  stroke-dasharray: 5;
  animation: dashdraw 0.5s linear infinite;
}

@keyframes dashdraw {
  from {
    stroke-dashoffset: 10;
  }
  to {
    stroke-dashoffset: 0;
  }
}
</style>
