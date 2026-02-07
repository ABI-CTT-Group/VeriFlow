<script setup lang="ts">
/**
 * GraphNode.vue
 * Ported from: planning/UI/src/components/GraphNode.tsx
 * 
 * Workflow graph node component with inputs/outputs and status indicators.
 * Adapted for Vue Flow Custom Node.
 */
import { Database, Beaker, Box, CheckCircle, Loader, Clock, AlertCircle } from 'lucide-vue-next'
import { Handle, Position } from '@vue-flow/core'
import { inject } from 'vue'

// Vue Flow passes node data via `data` prop, and other props like `selected`
interface Props {
  id: string
  data: any
  selected: boolean 
}

const props = defineProps<Props>()

// Emits from Vue Flow custom nodes don't easily bubble, so we use injected handlers
const onDatasetSelect = inject<(datasetId: string) => void>('onDatasetSelect')

const availableDatasets = [
  { id: 'dce-mri-scans', name: 'DCE-MRI Scans', samples: ['Subject_001/T1w.nii.gz', 'Subject_002/T1w.nii.gz'] },
  { id: 'tumor-segmentation', name: 'Tumor Segmentation', samples: ['Subject_001/tumor_mask.nii.gz', 'Subject_002/tumor_mask.nii.gz'] }
]

function getSampleDisplayName(samplePath: string): string {
  return samplePath.split('/').pop() || samplePath
}

function getStatusColor(): string {
  if (props.data.type !== 'tool') return 'border-slate-300'
  
  switch (props.data.status) {
    case 'completed': return 'border-green-300 bg-green-50'
    case 'running': return 'border-blue-300 bg-blue-50'
    case 'error': return 'border-red-300 bg-red-50'
    default: return 'border-slate-300'
  }
}

function handleDatasetSelect(datasetId: string, event: MouseEvent) {
  event.stopPropagation()
  if (onDatasetSelect) {
    onDatasetSelect(datasetId)
  }
}
</script>

<template>
  <div
    :class="[
      'bg-white rounded-xl border-2 transition-all duration-200 ease-in-out',
      selected ? 'border-blue-500 shadow-xl ring-1 ring-blue-500/20' : getStatusColor() + ' shadow-sm hover:border-blue-300 hover:shadow-md',
      data.type === 'measurement' ? 'cursor-default' : 'cursor-pointer'
    ]"
    :style="{ 
      width: '280px'
    }"
  >
    <!-- Header -->
    <div class="px-4 py-3 border-b border-slate-200">
      <div class="flex items-start justify-between">
        <div class="flex items-center gap-2 flex-1 min-w-0">
          <!-- Node Icon -->
          <Database v-if="data.type === 'measurement'" class="w-5 h-5 text-blue-600" />
          <Beaker v-else-if="data.type === 'tool'" class="w-5 h-5 text-purple-600" />
          <Box v-else class="w-5 h-5 text-green-600" />
          
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-slate-900 truncate">{{ data.name }}</p>
            <p v-if="data.confidence" class="text-xs text-slate-500 mt-0.5">
              Confidence: {{ (data.confidence * 100).toFixed(0) }}%
            </p>
            <p v-if="data.totalSubjects" class="text-xs text-slate-500 mt-0.5">
              {{ data.totalSubjects }} subjects available
            </p>
          </div>
        </div>
        
        <!-- Status Icon -->
        <CheckCircle v-if="data.status === 'completed'" class="w-4 h-4 text-green-600" />
        <Loader v-else-if="data.status === 'running'" class="w-4 h-4 text-blue-600 animate-spin" />
        <Clock v-else-if="data.status === 'pending'" class="w-4 h-4 text-slate-400" />
        <AlertCircle v-else-if="data.status === 'error'" class="w-4 h-4 text-red-600" />
      </div>
    </div>

    <!-- Body -->
    <div class="p-3">
      <!-- Input Ports -->
      <div v-if="data.inputs && data.inputs.length > 0" class="space-y-2 mb-3">
        <p v-if="data.role !== 'output'" class="text-xs font-medium text-slate-600">Inputs</p>
        
        <div v-for="input in data.inputs" :key="input.id" class="relative">
          <!-- Dataset Input -->
          <div 
            v-if="input.datasetId"
            :class="[
              'border rounded-lg p-2 bg-white cursor-pointer transition-all',
              data.selectedDatasetId === input.datasetId 
                ? 'border-blue-500 shadow-md ring-2 ring-blue-200' 
                : 'border-slate-200 hover:border-blue-300 hover:shadow-sm'
            ]"
            @click="handleDatasetSelect(input.datasetId, $event)"
          >
            <!-- Input Port Handle -->
            <Handle
              type="target"
              :position="Position.Left"
              :id="input.id"
              class="!w-4 !h-4 !bg-white !border-2 !border-slate-400 hover:!border-blue-500 hover:!bg-blue-50 hover:!scale-125 transition-all !-left-6"
            />
            
            <div class="flex-1 space-y-1.5">
              <div>
                <label class="text-xs text-slate-500 block mb-1">Dataset</label>
                <select 
                  class="w-full px-2 py-1 border border-slate-300 rounded text-xs bg-white hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  :value="input.datasetId"
                  @click.stop
                  disabled
                >
                  <option v-for="ds in availableDatasets" :key="ds.id" :value="ds.id">
                    {{ ds.name }}
                  </option>
                </select>
              </div>
              <div v-if="input.sampleId">
                <label class="text-xs text-slate-500 block mb-1">Sample</label>
                <select 
                  class="w-full px-2 py-1 border border-slate-300 rounded text-xs bg-white hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  :value="input.sampleId"
                  @click.stop
                  disabled
                >
                  <option 
                    v-for="sample in availableDatasets.find(ds => ds.id === input.datasetId)?.samples" 
                    :key="sample" 
                    :value="sample"
                  >
                    {{ getSampleDisplayName(sample) }}
                  </option>
                </select>
              </div>
            </div>
          </div>
          
          <!-- Simple Input -->
          <div v-else class="flex items-center gap-2">
            <Handle
              type="target"
              :position="Position.Left"
              :id="input.id"
              class="!w-4 !h-4 !bg-white !border-2 !border-slate-400 hover:!border-blue-500 hover:!bg-blue-50 hover:!scale-125 transition-all !-left-6"
            />
            <div class="flex-1 text-xs px-2 py-1.5 bg-slate-50 border border-slate-200 rounded">
              {{ input.label }}
            </div>
          </div>
        </div>
      </div>

      <!-- Output Ports -->
      <div v-if="data.outputs && data.outputs.length > 0" class="space-y-2">
        <p v-if="data.role !== 'input'" class="text-xs font-medium text-slate-600">Outputs</p>
        
        <div v-for="output in data.outputs" :key="output.id" class="relative">
          <!-- Dataset Output -->
          <div 
            v-if="output.datasetId"
            :class="[
              'border rounded-lg p-2 bg-white cursor-pointer transition-all',
              data.selectedDatasetId === output.datasetId 
                ? 'border-blue-500 shadow-md ring-2 ring-blue-200' 
                : 'border-slate-200 hover:border-blue-300 hover:shadow-sm'
            ]"
            @click="handleDatasetSelect(output.datasetId, $event)"
          >
            <div class="flex-1 space-y-1.5">
              <div>
                <label class="text-xs text-slate-500 block mb-1">Dataset</label>
                <select 
                  class="w-full px-2 py-1 border border-slate-300 rounded text-xs bg-white hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  :value="output.datasetId"
                  @click.stop
                  disabled
                >
                  <option v-for="ds in availableDatasets" :key="ds.id" :value="ds.id">
                    {{ ds.name }}
                  </option>
                </select>
              </div>
              <div v-if="output.sampleId">
                <label class="text-xs text-slate-500 block mb-1">Sample</label>
                <select 
                  class="w-full px-2 py-1 border border-slate-300 rounded text-xs bg-white hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  :value="output.sampleId"
                  @click.stop
                  disabled
                >
                  <option 
                    v-for="sample in availableDatasets.find(ds => ds.id === output.datasetId)?.samples" 
                    :key="sample" 
                    :value="sample"
                  >
                    {{ getSampleDisplayName(sample) }}
                  </option>
                </select>
              </div>
            </div>
            <!-- Output Port Handle -->
            <Handle
              type="source"
              :position="Position.Right"
              :id="output.id"
              class="!w-4 !h-4 !bg-white !border-2 !border-slate-400 hover:!border-blue-500 hover:!bg-blue-50 hover:!scale-125 transition-all !-right-6"
            />
          </div>
          
          <!-- Simple Output -->
          <div v-else class="flex items-center gap-2">
            <div class="flex-1 text-xs px-2 py-1.5 bg-slate-50 border border-slate-200 rounded">
              {{ output.label }}
            </div>
            <Handle
              type="source"
              :position="Position.Right"
              :id="output.id"
              class="!w-4 !h-4 !bg-white !border-2 !border-slate-400 hover:!border-blue-500 hover:!bg-blue-50 hover:!scale-125 transition-all !-right-6"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
