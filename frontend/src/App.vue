<script setup lang="ts">
/**
 * VeriFlow - Main Application Component
 * Ported from: planning/UI/src/App.tsx
 * 
 * Contains the main 4-panel layout with resizable console and collapsible panels.
 */
import { ref, watch } from 'vue'
import { ChevronRight, ChevronDown, ChevronUp } from 'lucide-vue-next'
import { storeToRefs } from 'pinia'
import { useWorkflowStore } from './stores/workflow'

// Layout components
import ResizablePanel from './components/layout/ResizablePanel.vue'
import CollapsibleHorizontalPanel from './components/layout/CollapsibleHorizontalPanel.vue'

// Module components
import UploadModule from './components/modules/UploadModule.vue'
import StudyDesignModule from './components/modules/StudyDesignModule.vue'
import ConsoleModule from './components/modules/ConsoleModule.vue'
import ConfigurationPanel from './components/modules/ConfigurationPanel.vue'
import DatasetNavigationModule from './components/modules/DatasetNavigationModule.vue'

// Workflow components
import WorkflowAssemblerModule from './components/workflow/WorkflowAssemblerModule.vue'

// Initialize Store
const store = useWorkflowStore()
const {
  isLeftPanelCollapsed,
  isAssembled,
  isWorkflowRunning,
  isConsoleCollapsed,
  consoleHeight,
  selectedNode,
  selectedAssay,
  selectedDatasetId,
  hasUploadedFiles,
  viewerPdfUrl,
  isViewerVisible,
  isLoading,
  isRightPanelCollapsed: isDatasetNavCollapsed // Map store name to component local name preference
} = storeToRefs(store)

const {
  assembleWorkflow,
  runWorkflow,
  loadExample,
  // toggleRightPanel,
  // toggleConsole,
  // updateNodeStatus
} = store

// Local UI state not in store (or specific to App.vue layout logic)
const activePropertyId = ref<string>('')
const shouldCollapseViewer = ref(false)
const collapseAllExceptSelected = ref(false)
const isResizingConsole = ref(false)
const defaultViewerPlugin = ref('auto')

// Handler functions
function handleSourceClick(propertyId: string) {
  // Update store state via direct mutation (or action if preferred)
  store.viewerPdfUrl = store.uploadedPdfUrl
  store.isViewerVisible = false
  setTimeout(() => {
    store.isViewerVisible = true
  }, 0)
  activePropertyId.value = propertyId
  shouldCollapseViewer.value = false
  // if (isWorkflowCollapsed.value) { ... } // Revisit if workflow collapse is needed
}

function handleViewerClose() {
  store.isViewerVisible = false
  activePropertyId.value = ''
}

function handlePdfUpload(pdfUrl: string) {
  // In a real flow, UploadModule calls the store action directly or emits file.
  // If UploadModule emits 'pdfUpload', we update the store.
  // However, UploadModule should ideally use the store directly for the upload action.
  // For now, syncing the emitted url to store.
  store.uploadedPdfUrl = pdfUrl
  store.hasUploadedFiles = true
}

// Stage 6: Load MAMA-MIA Demo
function handleLoadDemo() {
  loadExample('mama-mia')
}

function handleAssembleClick() {
  if (selectedAssay.value) {
    assembleWorkflow(selectedAssay.value)
  }
  // isAssembled set by store action
  store.isViewerVisible = false
  activePropertyId.value = ''
  shouldCollapseViewer.value = true
  store.isLeftPanelCollapsed = true
}

function handleRunWorkflow() {
  runWorkflow()
  collapseAllExceptSelected.value = true
  isDatasetNavCollapsed.value = false // Auto-expand results panel
}

function handleSelectNode(node: any) {
  store.selectedNode = node
}

function handleDatasetSelect(datasetId: string | null) {
  store.selectedDatasetId = datasetId ?? null
}

// Console resize handlers
function handleConsoleMouseDown(e: MouseEvent) {
  e.preventDefault()
  isResizingConsole.value = true
}

function handleMouseMove(e: MouseEvent) {
  if (isResizingConsole.value) {
    const newHeight = window.innerHeight - e.clientY
    const minHeight = 100
    const maxHeight = window.innerHeight - 200
    store.consoleHeight = Math.min(Math.max(newHeight, minHeight), maxHeight)
  }
}

function handleMouseUp() {
  isResizingConsole.value = false
}

// Watchers for UI state consistency
watch(isDatasetNavCollapsed, (val) => {
  store.isRightPanelCollapsed = val
})
</script>

<template>
  <div 
    class="h-screen flex flex-col bg-slate-50 overflow-hidden"
    @mousemove="handleMouseMove"
    @mouseup="handleMouseUp"
  >
    <!-- Header -->
    <header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between flex-shrink-0 shadow-sm z-10">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 bg-blue-600 rounded flex items-center justify-center">
          <span class="text-white font-bold text-sm">VF</span>
        </div>
        <div>
          <h1 class="font-semibold text-slate-900">VeriFlow</h1>
          <p class="text-xs text-slate-500">Research Reproducibility Engineer</p>
        </div>
      </div>
      <ConfigurationPanel 
        :default-viewer-plugin="defaultViewerPlugin"
        @viewer-plugin-change="defaultViewerPlugin = $event"
      />
    </header>

    <!-- Main Content -->
    <div class="flex-1 flex overflow-hidden min-h-0">
      <!-- Left Panel - Upload & Review Study Design -->
      <ResizablePanel
        v-if="!isLeftPanelCollapsed"
        side="left"
        :default-width="320"
        :min-width="280"
        :max-width="600"
      >
        <div class="h-full flex flex-col bg-white border-r border-slate-200 overflow-hidden">
          <UploadModule 
            @pdf-upload="handlePdfUpload"
            @collapse-left-panel="isLeftPanelCollapsed = true"
            @load-demo="handleLoadDemo"
            :has-uploaded-files="hasUploadedFiles"
            :is-loading="isLoading"
          />
          <StudyDesignModule 
            :selected-assay="selectedAssay"
            :has-uploaded-files="hasUploadedFiles"
            @select-assay="selectedAssay = $event"
            @source-click="handleSourceClick"
            @assemble-click="handleAssembleClick"
            @collapse-left-panel="isLeftPanelCollapsed = true"
          />
        </div>
      </ResizablePanel>

      <!-- Collapsed left panel -->
      <div v-else class="w-8 bg-slate-50 border-r border-slate-200 flex-shrink-0">
        <button
          @click="isLeftPanelCollapsed = false"
          class="h-full w-full hover:bg-slate-100 transition-colors flex items-center justify-center"
        >
          <span 
            class="text-xs font-medium text-slate-600 whitespace-nowrap" 
            style="writing-mode: vertical-rl; transform: rotate(180deg)"
          >
            Upload &amp; Review Study Design
          </span>
        </button>
      </div>

      <!-- Middle Panel - Workflow Assembler -->
      <div class="flex-1 flex flex-col bg-white overflow-hidden min-w-0">
        <WorkflowAssemblerModule
          :selected-assay="selectedAssay"
          :selected-node="selectedNode"
          :viewer-pdf-url="viewerPdfUrl"
          :is-viewer-visible="isViewerVisible"
          :active-property-id="activePropertyId"
          :is-assembled="isAssembled"
          :should-collapse-viewer="shouldCollapseViewer"
          :has-uploaded-files="hasUploadedFiles"
          :is-workflow-running="isWorkflowRunning"
          :default-viewer-plugin="defaultViewerPlugin"
          :selected-dataset-id="selectedDatasetId"
          @select-node="handleSelectNode"
          @viewer-close="handleViewerClose"
          @catalogue-source-click="handleSourceClick"
          @run-workflow="handleRunWorkflow"
          @dataset-select="handleDatasetSelect"
        />
      </div>

      <!-- Right Panel - Visualise and Export Results -->
      <CollapsibleHorizontalPanel
        :is-collapsed="isDatasetNavCollapsed"
        @toggle="isDatasetNavCollapsed = !isDatasetNavCollapsed"
        side="right"
        :default-width="320"
        label="Visualise and Export Results"
      >
        <div class="h-full flex flex-col bg-white border-l border-slate-200 overflow-hidden">
          <!-- Header with inline chevron -->
          <div class="px-4 py-3 border-b border-slate-200 flex-shrink-0">
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-slate-700">4. Visualise and Export Results</span>
              <button
                @click="isDatasetNavCollapsed = true"
                class="text-slate-400 hover:text-slate-600 transition-colors"
              >
                <ChevronRight class="w-4 h-4" />
              </button>
            </div>
            <p class="text-xs text-slate-400 mt-0.5">Select a Workflow Item to View it's Results</p>
          </div>

          <!-- Content -->
          <div class="flex-1 flex flex-col overflow-hidden">
            <DatasetNavigationModule 
              :selected-node="selectedNode"
              :default-viewer-plugin="defaultViewerPlugin"
              :selected-dataset-id="selectedDatasetId"
            />
          </div>
        </div>
      </CollapsibleHorizontalPanel>
    </div>

    <!-- Bottom Panel - Console -->
    <div 
      v-if="!isConsoleCollapsed"
      class="border-t border-slate-200 flex-shrink-0 bg-white relative" 
      :style="{ height: consoleHeight + 'px' }"
    >
      <!-- Resize handle -->
      <div
        @mousedown="handleConsoleMouseDown"
        class="absolute top-0 left-0 right-0 h-1 cursor-ns-resize hover:bg-blue-500 transition-colors z-20"
      />
      <div class="h-full flex flex-col overflow-hidden" style="padding-top: 4px">
        <!-- Header with collapse button -->
        <div class="px-4 py-2 flex items-center justify-between flex-shrink-0">
          <div class="flex items-center gap-2">
            <button
              @click="isConsoleCollapsed = true"
              class="text-slate-400 hover:text-slate-600 transition-colors"
            >
              <ChevronDown class="w-4 h-4" />
            </button>
            <span class="text-sm font-medium text-slate-700">Console</span>
          </div>
        </div>
        <!-- Content -->
        <div class="flex-1 overflow-hidden">
          <ConsoleModule />
        </div>
      </div>
    </div>
    <div 
      v-else
      class="border-t border-slate-200 flex-shrink-0 bg-slate-50" 
      style="height: 32px"
    >
      <button
        @click="isConsoleCollapsed = false"
        class="w-full h-full hover:bg-slate-100 transition-colors flex items-center justify-center gap-2"
      >
        <ChevronUp class="w-4 h-4 text-slate-600" />
        <span class="text-xs font-medium text-slate-600">Console</span>
      </button>
    </div>
  </div>
</template>
