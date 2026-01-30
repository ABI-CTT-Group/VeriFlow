
<script setup lang="ts">
/**
 * GraphNode.vue
 * Ported from: planning/UI/src/components/GraphNode.tsx
 * 
 * Workflow graph node component with inputs/outputs and status indicators.
 */
import { Database, Beaker, Box, CheckCircle, Loader, Clock, AlertCircle } from 'lucide-vue-next'

interface Props {
  node: any
  isSelected: boolean
  selectedDatasetId?: string | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  select: []
  portMouseDown: [nodeId: string, portId: string, portType: 'input' | 'output', event: MouseEvent]
  portMouseUp: [nodeId: string, portId: string, portType: 'input' | 'output']
  datasetSelect: [datasetId: string]
}>()

const availableDatasets = [
  { id: 'dce-mri-scans', name: 'DCE-MRI Scans', samples: ['Subject_001/T1w.nii.gz', 'Subject_002/T1w.nii.gz'] },
  { id: 'tumor-segmentation', name: 'Tumor Segmentation', samples: ['Subject_001/tumor_mask.nii.gz', 'Subject_002/tumor_mask.nii.gz'] }
]

function getSampleDisplayName(samplePath: string): string {
  return samplePath.split('/').pop() || samplePath
}

function getStatusColor(): string {
  if (props.node.type !== 'tool') return 'border-slate-300'
  
  switch (props.node.data?.status) {
    case 'completed': return 'border-green-300 bg-green-50'
    case 'running': return 'border-blue-300 bg-blue-50'
    case 'error': return 'border-red-300 bg-red-50'
    default: return 'border-slate-300'
  }
}

function handleNodeClick(e: MouseEvent) {
  if (props.node.type === 'measurement') {
    e.stopPropagation()
    return
  }
  emit('select')
}

function handlePortMouseDown(portId: string, portType: 'input' | 'output', event: MouseEvent) {
  emit('portMouseDown', props.node.id, portId, portType, event)
}

function handlePortMouseUp(portId: string, portType: 'input' | 'output') {
  emit('portMouseUp', props.node.id, portId, portType)
}

function handleDatasetSelect(datasetId: string, event: MouseEvent) {
  event.stopPropagation()
  emit('datasetSelect', datasetId)
}
</script>

<template>
  <div
    @click="handleNodeClick"
    :class="[
      'absolute bg-white rounded-xl border-2 transition-all duration-200 ease-in-out',
      isSelected ? 'border-blue-500 shadow-xl ring-1 ring-blue-500/20' : getStatusColor() + ' shadow-sm hover:border-blue-300 hover:shadow-md',
      node.type === 'measurement' ? 'cursor-default' : 'cursor-pointer'
    ]"
    :style="{ 
      left: node.position.x + 'px', 
      top: node.position.y + 'px',
      width: '280px'
    }"
  >
    <!-- Header -->
    <div class="px-4 py-3 border-b border-slate-200">
      <div class="flex items-start justify-between">
        <div class="flex items-center gap-2 flex-1 min-w-0">
          <!-- Node Icon -->
          <Database v-if="node.type === 'measurement'" class="w-5 h-5 text-blue-600" />
          <Beaker v-else-if="node.type === 'tool'" class="w-5 h-5 text-purple-600" />
          <Box v-else class="w-5 h-5 text-green-600" />
          
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-slate-900 truncate">{{ node.data?.name }}</p>
            <p v-if="node.data?.confidence" class="text-xs text-slate-500 mt-0.5">
              Confidence: {{ (node.data.confidence * 100).toFixed(0) }}%
            </p>
            <p v-if="node.data?.totalSubjects" class="text-xs text-slate-500 mt-0.5">
              {{ node.data.totalSubjects }} subjects available
            </p>
          </div>
        </div>
        
        <!-- Status Icon -->
        <CheckCircle v-if="node.data?.status === 'completed'" class="w-4 h-4 text-green-600" />
        <Loader v-else-if="node.data?.status === 'running'" class="w-4 h-4 text-blue-600 animate-spin" />
        <Clock v-else-if="node.data?.status === 'pending'" class="w-4 h-4 text-slate-400" />
        <AlertCircle v-else-if="node.data?.status === 'error'" class="w-4 h-4 text-red-600" />
      </div>
    </div>

    <!-- Body -->
    <div class="p-3">
      <!-- Input Ports -->
      <div v-if="node.data?.inputs && node.data.inputs.length > 0" class="space-y-2 mb-3">
        <p v-if="node.data?.role !== 'output'" class="text-xs font-medium text-slate-600">Inputs</p>
        
        <div v-for="input in node.data.inputs" :key="input.id" class="relative">
          <!-- Dataset Input -->
          <div 
            v-if="input.datasetId"
            :class="[
              'border rounded-lg p-2 bg-white cursor-pointer transition-all',
              selectedDatasetId === input.datasetId 
                ? 'border-blue-500 shadow-md ring-2 ring-blue-200' 
                : 'border-slate-200 hover:border-blue-300 hover:shadow-sm'
            ]"
            @click="handleDatasetSelect(input.datasetId, $event)"
          >
            <!-- Input Port Circle -->
            <div
              class="absolute -left-6 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 border-slate-400 bg-white cursor-crosshair hover:border-blue-500 hover:bg-blue-50 hover:scale-125 transition-all z-10"
              @mouseup="handlePortMouseUp(input.id, 'input')"
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
            <div
              class="absolute -left-6 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 border-slate-400 bg-white cursor-crosshair hover:border-blue-500 hover:bg-blue-50 hover:scale-125 transition-all z-10"
              @mouseup="handlePortMouseUp(input.id, 'input')"
            />
            <div class="flex-1 text-xs px-2 py-1.5 bg-slate-50 border border-slate-200 rounded">
              {{ input.label }}
            </div>
          </div>
        </div>
      </div>

      <!-- Output Ports -->
      <div v-if="node.data?.outputs && node.data.outputs.length > 0" class="space-y-2">
        <p v-if="node.data?.role !== 'input'" class="text-xs font-medium text-slate-600">Outputs</p>
        
        <div v-for="output in node.data.outputs" :key="output.id" class="relative">
          <!-- Dataset Output -->
          <div 
            v-if="output.datasetId"
            :class="[
              'border rounded-lg p-2 bg-white cursor-pointer transition-all',
              selectedDatasetId === output.datasetId 
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
            <!-- Output Port Circle -->
            <div
              class="absolute -right-6 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 border-slate-400 bg-white cursor-crosshair hover:border-blue-500 hover:bg-blue-50 hover:scale-125 transition-all z-10"
              @mousedown="handlePortMouseDown(output.id, 'output', $event)"
            />
          </div>
          
          <!-- Simple Output -->
          <div v-else class="flex items-center gap-2">
            <div class="flex-1 text-xs px-2 py-1.5 bg-slate-50 border border-slate-200 rounded">
              {{ output.label }}
            </div>
            <div
              class="absolute -right-6 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 border-slate-400 bg-white cursor-crosshair hover:border-blue-500 hover:bg-blue-50 hover:scale-125 transition-all z-10"
              @mousedown="handlePortMouseDown(output.id, 'output', $event)"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
