<script setup lang="ts">
/**
 * WorkflowAssemblerModule.vue
 * Ported from: planning/UI/src/components/WorkflowAssemblerModule.tsx
 * 
 * Main workflow canvas with nodes, connections, and execution controls.
 * Refactored to use @vue-flow/core for robust zoom/pan and graph management.
 */
import { ref, watch, markRaw } from 'vue'
import { Play, Square, Download, ChevronLeft } from 'lucide-vue-next'
import { storeToRefs } from 'pinia'
import { VueFlow, type Edge, type Connection } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

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
  hasUploadedFiles?: boolean
  isWorkflowRunning?: boolean
  defaultViewerPlugin?: string
  selectedDatasetId?: string | null
  shouldCollapseViewer?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  selectedAssay: null,
  selectedNode: null,
  viewerPdfUrl: null,
  isViewerVisible: false,
  activePropertyId: undefined,
  hasUploadedFiles: false,
  isWorkflowRunning: false,
  defaultViewerPlugin: 'auto',
  selectedDatasetId: null,
  shouldCollapseViewer: false,
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
  edges: storeEdges, 
  isAssembled,
  isWorkflowRunning
} = storeToRefs(store)
const { runWorkflow, stopWorkflow } = store

// Local UI state
const numSubjects = ref(1)
const isViewerCollapsed = ref(!props.isViewerVisible)
const isCatalogueCollapsed = ref(false)

// Provide handlers for child nodes
import { provide } from 'vue'
provide('onDatasetSelect', (datasetId: string) => {
  emit('datasetSelect', datasetId)
})

// Vue Flow State
// We wrap components in markRaw to avoid Vue reactivity overhead on component definitions
const nodeTypes = {
  tool: markRaw(GraphNode),
  measurement: markRaw(GraphNode),
  dataset: markRaw(GraphNode),
  default: markRaw(GraphNode)
} as any

const edgeTypes = {
  default: markRaw(ConnectionLine)
}

const vueFlowInstance = ref<any>(null)

// Watchers
watch(() => props.isViewerVisible, (visible) => {
  if (visible) {
    isViewerCollapsed.value = false
  }
})

watch(() => props.shouldCollapseViewer, (shouldCollapse) => {
  if (shouldCollapse) {
    isViewerCollapsed.value = true
  }
})

// Handlers
function handleRunWorkflow() {
  runWorkflow() // Call store action
  emit('runWorkflow') // Keep emit for parent UI updates if needed
}

function handleStopWorkflow() {
  stopWorkflow() // Call store action
}

function onPaneReady(instance: any) {
  vueFlowInstance.value = instance
  instance.fitView()
}

// Handle new connections
function onConnectHandler(params: Connection) {
  const newEdge: Edge = {
    id: `e-${params.source}-${params.target}-${Date.now()}`,
    source: params.source,
    target: params.target,
    sourceHandle: params.sourceHandle,
    targetHandle: params.targetHandle,
    type: 'default'
  }
  store.edges.push(newEdge)
}

function handleDeleteConnection(connectionId: string) {
  store.edges = store.edges.filter(c => c.id !== connectionId)
}

// Drag and Drop
function onDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'copy'
  }
}

function onDrop(event: DragEvent) {
  const data = event.dataTransfer?.getData('application/json')
  if (!data) return
  
  try {
    const { item, type } = JSON.parse(data)
    
    // Project mouse coordinates to flow coordinates
    // We need the bounding rect of the flow container to calculate relative position first
    // Note: useVueFlow's project assumes coordinates relative to the flow pane (usually) or requires adjustment
    // But better: use screenToFlowCoordinate if available from specific instance APIs or manually calculate.
    // simpler approach with project:
    if (!vueFlowInstance.value) return 

    // Get bounds of the flow wrapper
    // We can rely on event properties directly for projection if we have the instance
    const position = vueFlowInstance.value.screenToFlowCoordinate({
      x: event.clientX,
      y: event.clientY,
    })
    
    // Create new node compatible with Vue Flow structure
    const newNode: any = { 
      id: `${type}-${Date.now()}`,
      type: type, // This triggers the correct node type mapping
      position,
      data: {
        name: item.name,
        status: 'pending',
        type: type, // Redundant but useful for data access inside GraphNode
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

function handleNodeClick(event: any) {
  emit('selectNode', event.node)
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
            max="2"
            v-model="numSubjects"
            class="w-16 px-2 py-1 text-xs border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <span class="text-xs text-slate-500">/ 2</span>
        </div>
        <div class="w-px h-6 bg-slate-200"></div>
        <div class="flex items-center gap-2">
          <button
            v-if="!isWorkflowRunning"
            @click="handleRunWorkflow"
            class="px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700 transition-colors flex items-center gap-1.5"
          >
            <Play class="w-3.5 h-3.5" />
            Run Workflow
          </button>
          <button
            v-else
            @click="handleStopWorkflow"
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

      <!-- Canvas (Center) - Vue Flow Implemenation -->
      <div class="flex-1 h-full w-full relative bg-slate-50" @dragover="onDragOver" @drop="onDrop">
        <VueFlow
          v-model="nodes"
          v-model:edges="storeEdges"
          :node-types="nodeTypes"
          :edge-types="edgeTypes"
          :default-viewport="{ zoom: 1 }"
          :min-zoom="0.2"
          :max-zoom="4"
          @pane-ready="onPaneReady"
          @connect="onConnectHandler"
          @node-click="handleNodeClick"
          fit-view-on-init
          class="h-full w-full"
        >
          <Background pattern-color="#e2e8f0" :gap="16" />
          <Controls />
          <MiniMap />
          
          <!-- Edge Delete Handler - passed via custom edge emit -->
          <template #edge-default="props">
            <ConnectionLine v-bind="props" @delete="handleDeleteConnection" />
          </template>
        </VueFlow>
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
