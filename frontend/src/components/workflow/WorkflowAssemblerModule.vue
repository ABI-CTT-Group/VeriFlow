<script setup lang="ts">
/**
 * WorkflowAssemblerModule.vue
 * Ported from: planning/UI/src/components/WorkflowAssemblerModule.tsx
 * 
 * Main workflow canvas with nodes, connections, and execution controls.
 */
import { ref, watch } from 'vue'
import { Play, Square, Download, ChevronLeft } from 'lucide-vue-next'
import { storeToRefs } from 'pinia'
import type { Edge } from '@vue-flow/core'
import { useWorkflowStore } from '../../stores/workflow'
import GraphNode from './GraphNode.vue'
import ConnectionLine from './ConnectionLine.vue'
import DataObjectCatalogue from './DataObjectCatalogue.vue'
import ViewerPanel from '../modules/ViewerPanel.vue'
import ResizablePanel from '../layout/ResizablePanel.vue'

// Props
interface Props {
  selectedAssay: string | null
  selectedNode: any
  viewerPdfUrl?: string | null
  isViewerVisible?: boolean
  activePropertyId?: string
  // isAssembled?: boolean // Unused, coming from store usually, but kept for compatibility if needed. Actually removal is cleaner.
  hasUploadedFiles?: boolean
  isWorkflowRunning?: boolean
  defaultViewerPlugin?: string
  selectedDatasetId?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  selectedAssay: null,
  selectedNode: null,
  viewerPdfUrl: null,
  isViewerVisible: false,
  activePropertyId: undefined,
  // isAssembled: false,
  hasUploadedFiles: false,
  isWorkflowRunning: false,
  defaultViewerPlugin: 'auto',
  selectedDatasetId: null,
})

const emit = defineEmits<{
  selectNode: [node: any]
  viewerClose: []
  catalogueSourceClick: [propertyId: string]
  runWorkflow: []
  datasetSelect: [datasetId: string | null]
}>()

// Store
const store = useWorkflowStore()
const { 
  nodes, 
  edges: storeEdges, // Rename to avoid conflict if we used edges locally, though inconsistent with other usage. Keeping storeEdges for clarity.
  isAssembled 
} = storeToRefs(store)
const { runWorkflow } = store

// Local UI state
const isRunning = ref(false)
const numSubjects = ref(1)
const isViewerCollapsed = ref(!props.isViewerVisible)
const isCatalogueCollapsed = ref(false)
const canvasRef = ref<HTMLDivElement | null>(null)
const dragConnection = ref<{ sourceNodeId: string; sourcePortId: string; x: number; y: number } | null>(null)

// Watchers
watch(() => props.isViewerVisible, (visible) => {
  if (visible) {
    isViewerCollapsed.value = false
  }
})

// Handlers
function handleRunWorkflow() {
  isRunning.value = true
  runWorkflow() // Call store action
  emit('runWorkflow') // Keep emit for parent UI updates if needed
}

function handleDeleteConnection(connectionId: string) {
  store.edges = store.edges.filter(c => c.id !== connectionId)
}

function handlePortMouseDown(nodeId: string, portId: string, portType: 'input' | 'output', event: MouseEvent) {
  if (portType === 'output' && canvasRef.value) {
    event.stopPropagation()
    const rect = canvasRef.value.getBoundingClientRect()
    dragConnection.value = {
      sourceNodeId: nodeId,
      sourcePortId: portId,
      x: event.clientX - rect.left,
      y: event.clientY - rect.top
    }
  }
}

function handleMouseMove(event: MouseEvent) {
  if (dragConnection.value && canvasRef.value) {
    const rect = canvasRef.value.getBoundingClientRect()
    dragConnection.value = {
      ...dragConnection.value,
      x: event.clientX - rect.left,
      y: event.clientY - rect.top
    }
  }
}

function handlePortMouseUp(nodeId: string, portId: string, portType: 'input' | 'output') {
  if (dragConnection.value && portType === 'input') {
    // Add to store edges
    const newEdge: Edge = {
      id: `conn-${Date.now()}`,
      source: dragConnection.value.sourceNodeId,
      sourceHandle: dragConnection.value.sourcePortId,
      target: nodeId,
      targetHandle: portId
    }
    store.edges.push(newEdge)
  }
  dragConnection.value = null
}

function handleMouseUp() {
  dragConnection.value = null
}

function onDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'copy'
  }
}

function onDrop(event: DragEvent) {
  if (!canvasRef.value) return
  
  const data = event.dataTransfer?.getData('application/json')
  if (!data) return
  
  try {
    const { item, type } = JSON.parse(data)
    const rect = canvasRef.value.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top
    
    // Create new node compatible with Vue Flow structure
    const newNode: any = { // Using any to bypass strict type checking against standard Node for custom props
      id: `${type}-${Date.now()}`,
      type: type,
      position: { x, y },
      data: {
        name: item.name,
        status: 'pending',
        inputs: type === 'tool' ? [{ id: `in-${Date.now()}`, label: 'Input' }] : undefined,
        outputs: [{ id: `out-${Date.now()}`, label: 'Output' }]
      }
    }
    
    store.nodes.push(newNode)
    emit('selectNode', newNode)
  } catch (err) {
    console.error('Failed to parse drop data', err)
  }
}

// Helper to get connection line coordinates from Edge
function getConnectionCoords(edge: Edge) {
  if (!canvasRef.value) return null
  
  const sourceNode = nodes.value.find(n => n.id === edge.source)
  const targetNode = nodes.value.find(n => n.id === edge.target)
  if (!sourceNode || !targetNode) return null
  
  // Try to find DOM elements for ports
  const sourcePortId = `port-output-${edge.source}-${edge.sourceHandle}`
  const targetPortId = `port-input-${edge.target}-${edge.targetHandle}`
  
  const sourceEl = canvasRef.value.querySelector(`#${sourcePortId}`)
  const targetEl = canvasRef.value.querySelector(`#${targetPortId}`)
  
  if (sourceEl && targetEl) {
    const canvasRect = canvasRef.value.getBoundingClientRect()
    const sourceRect = sourceEl.getBoundingClientRect()
    const targetRect = targetEl.getBoundingClientRect()
    
    return {
      startX: sourceRect.left - canvasRect.left + sourceRect.width / 2,
      startY: sourceRect.top - canvasRect.top + sourceRect.height / 2,
      endX: targetRect.left - canvasRect.left + targetRect.width / 2,
      endY: targetRect.top - canvasRect.top + targetRect.height / 2
    }
  }
  
  // Fallback if DOM not ready (should generally not happen for rendered connections)
  return null
}
</script>

<template>
  <!-- Empty state - no assay selected -->
  <div v-if="!selectedAssay" class="h-full flex items-center justify-center text-slate-400 bg-slate-50">
    <div class="text-center">
      <svg class="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
      </svg>
      <p class="text-sm">{{ hasUploadedFiles ? "Select an assay from Study Design to assemble it's workflow" : "Upload a paper to begin" }}</p>
    </div>
  </div>

  <!-- Ready to assemble state -->
  <div v-else-if="!isAssembled && !isViewerVisible" class="h-full flex items-center justify-center text-slate-400 bg-slate-50">
    <div class="text-center">
      <svg class="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
      </svg>
      <p class="text-sm font-medium text-slate-600">Ready to assemble</p>
      <p class="text-xs mt-1">Click "Assemble Selected Assay" to generate the workflow</p>
    </div>
  </div>

  <!-- Main workflow view -->
  <div v-else class="flex-1 flex flex-col overflow-hidden bg-white min-h-0">
    <!-- Header -->
    <div class="px-4 py-3 border-b border-slate-200 flex items-center justify-between bg-white flex-shrink-0">
      <div>
        <span class="text-sm font-medium text-slate-700">3. Assemble, Review, and Validate Workflow</span>
        <p class="text-xs text-slate-500 mt-0.5">CWL Workflow Assembly & Validation</p>
      </div>
      
      <!-- Workflow Controls -->
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2">
          <label class="text-xs font-medium text-slate-700">Subjects:</label>
          <input
            type="number"
            min="1"
            max="384"
            v-model="numSubjects"
            class="w-16 px-2 py-1 text-xs border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <span class="text-xs text-slate-500">/ 384</span>
        </div>
        <div class="w-px h-6 bg-slate-200"></div>
        <div class="flex items-center gap-2">
          <button
            v-if="!isRunning"
            @click="handleRunWorkflow"
            class="px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700 transition-colors flex items-center gap-1.5"
          >
            <Play class="w-3.5 h-3.5" />
            Run Workflow
          </button>
          <button
            v-else
            @click="isRunning = false"
            class="px-3 py-1.5 bg-red-600 text-white text-xs font-medium rounded hover:bg-red-700 transition-colors flex items-center gap-1.5"
          >
            <Square class="w-3.5 h-3.5" />
            Stop
          </button>
          <button class="px-3 py-1.5 border border-slate-300 text-slate-700 text-xs font-medium rounded hover:bg-slate-50 transition-colors flex items-center gap-1.5">
            <Download class="w-3.5 h-3.5" />
            Export Workflow (CWL)
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content Area with 3 horizontal panels -->
    <div class="flex-1 flex overflow-hidden min-h-0">
      <!-- Viewer Panel (Collapsible) -->
      <template v-if="!isViewerCollapsed">
        <ResizablePanel
          side="left"
          :default-width="400"
          :min-width="300"
          :max-width="600"
        >
          <div class="h-full overflow-hidden bg-white relative">
            <div class="px-4 py-3 border-b border-slate-200 flex items-center justify-between bg-white flex-shrink-0">
              <div class="flex items-center gap-2">
                <button
                  @click="isViewerCollapsed = true"
                  class="text-slate-400 hover:text-slate-600 transition-colors"
                >
                  <ChevronLeft class="w-4 h-4" />
                </button>
                <span class="text-sm font-medium text-slate-700">Document Viewer</span>
              </div>
            </div>
            <div class="h-full overflow-hidden" style="padding-top: 52px;">
              <ViewerPanel 
                :pdf-url="isViewerVisible ? (viewerPdfUrl || undefined) : undefined"
                :active-property-id="activePropertyId"
                @close="emit('viewerClose')"
              />
            </div>
          </div>
        </ResizablePanel>
      </template>
      <div v-else class="w-8 bg-slate-50 border-r border-slate-200 flex-shrink-0">
        <button
          @click="isViewerCollapsed = false"
          class="h-full w-full hover:bg-slate-100 transition-colors flex items-center justify-center"
        >
          <span class="text-xs font-medium text-slate-600 whitespace-nowrap" style="writing-mode: vertical-rl; transform: rotate(180deg)">
            Document Viewer
          </span>
        </button>
      </div>

      <!-- Canvas (Center) -->
      <div 
        ref="canvasRef"
        class="flex-1 overflow-auto bg-slate-50 relative min-w-0"
        @mousemove="handleMouseMove"
        @mouseup="handleMouseUp"
        @mouseleave="handleMouseUp"
        @dragover="onDragOver"
        @drop="onDrop"
      >
        <div class="relative" style="width: 1600px; height: 600px;">
          <!-- Connection Lines -->
          <svg class="absolute inset-0 pointer-events-none" style="width: 100%; height: 100%;">
            <template v-for="edge in storeEdges" :key="edge.id">
              <ConnectionLine
                v-if="getConnectionCoords(edge)"
                :id="edge.id"
                :start-x="getConnectionCoords(edge)!.startX"
                :start-y="getConnectionCoords(edge)!.startY"
                :end-x="getConnectionCoords(edge)!.endX"
                :end-y="getConnectionCoords(edge)!.endY"
                @delete="handleDeleteConnection"
              />
            </template>
            
            <!-- Drag Connection -->
            <path
              v-if="dragConnection"
              :d="(() => {
                const sourceNode = nodes.find(n => n.id === dragConnection!.sourceNodeId);
                if (!sourceNode) return '';

                let startX = 0;
                let startY = 0;

                // Try to find the specific port element
                const portEl = canvasRef?.querySelector(`#port-output-${dragConnection!.sourceNodeId}-${dragConnection!.sourcePortId}`);
                
                if (portEl && canvasRef) {
                  const portRect = portEl.getBoundingClientRect();
                  const canvasRect = canvasRef.getBoundingClientRect();
                  startX = portRect.left - canvasRect.left + portRect.width / 2;
                  startY = portRect.top - canvasRect.top + portRect.height / 2;
                } else {
                   // Fallback calculation if DOM element not ready yet
                  const sourcePort = (sourceNode?.data as any)?.outputs?.find((p: any) => p.id === dragConnection!.sourcePortId);
                  const sourcePortIndex = (sourceNode.data as any).outputs?.indexOf(sourcePort) || 0;
                  startX = sourceNode.position.x + 280;
                  startY = sourceNode.position.y + 70 + sourcePortIndex * 28;
                }
                
                return `M ${startX} ${startY} C ${startX + 100} ${startY}, ${dragConnection.x - 100} ${dragConnection.y}, ${dragConnection.x} ${dragConnection.y}`;
              })()"
              stroke="#3b82f6"
              stroke-width="2"
              fill="none"
              stroke-dasharray="5,5"
            />
          </svg>

          <!-- Nodes -->
          <GraphNode
            v-for="node in nodes"
            :key="node.id"
            :node="node"
            :is-selected="selectedNode?.id === node.id"
            :selected-dataset-id="selectedDatasetId"
            @select="emit('selectNode', node)"
            @port-mouse-down="handlePortMouseDown"
            @port-mouse-up="handlePortMouseUp"
            @dataset-select="emit('datasetSelect', $event)"
          />
        </div>
      </div>

      <!-- Data Object Catalogue (Collapsible) -->
      <template v-if="!isCatalogueCollapsed">
        <ResizablePanel
          side="right"
          :default-width="320"
          :min-width="280"
          :max-width="500"
        >
          <DataObjectCatalogue 
            :active-workflow="true" 
            :selected-node-id="selectedNode?.id"
            :selected-dataset-id="selectedDatasetId"
            @source-click="emit('catalogueSourceClick', $event)"
            @dataset-select="emit('datasetSelect', $event)"
            @collapse="isCatalogueCollapsed = true"
          />
        </ResizablePanel>
      </template>
      <div v-else class="w-8 bg-slate-50 border-l border-slate-200 flex-shrink-0">
        <button
          @click="isCatalogueCollapsed = false"
          class="h-full w-full hover:bg-slate-100 transition-colors flex items-center justify-center"
        >
          <span class="text-xs font-medium text-slate-600 whitespace-nowrap" style="writing-mode: vertical-rl; transform: rotate(180deg)">
            Data Object Catalogue
          </span>
        </button>
      </div>
    </div>
  </div>
</template>
