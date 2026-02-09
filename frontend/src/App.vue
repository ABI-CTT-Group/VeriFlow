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
import LandingPageOverlay from './components/layout/LandingPageOverlay.vue'

// Module components
import UploadModule from './components/modules/UploadModule.vue'
import StudyDesignModule from './components/modules/StudyDesignModule.vue'
import ConsoleModule from './components/modules/ConsoleModule.vue'
import ConsoleInput from './components/modules/ConsoleInput.vue'
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
const showLandingPage = ref(true)
// Initialize visibility based on whether files are already uploaded (e.g. refresh)
const isStudyDesignVisible = ref(hasUploadedFiles.value)
// Initialize collapsed state: 
// The user wants it "default collapsed" but also mentions "Trigger button... then open".
// If we are starting fresh (invisible), it will open when made visible. 
// If we reload and it's visible, let's respect the "default collapsed" request if that's what "default" means here,
// OR since the user said "when Continue button clicked... trigger panel open", 
// we should probably start it as collapsed if it IS visible initially, unless we just completed the action.
// Let's stick to the prompt: "Default collapsed" might mean initial state if visible. 
const isStudyDesignCollapsed = ref(true)

// Handler functions
function handleUploadComplete() {
  isStudyDesignVisible.value = true
  isStudyDesignCollapsed.value = false // Open panel
  store.isLeftPanelCollapsed = true // Collapse Upload panel
}
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
  store.isConsoleCollapsed = false
}

function handleRunWorkflow() {
  runWorkflow()
  collapseAllExceptSelected.value = true
  isDatasetNavCollapsed.value = false // Auto-expand results panel
  isStudyDesignCollapsed.value = true
  shouldCollapseViewer.value = true
}

function handleSelectNode(node: any) {
  store.selectedNode = node
}

function handleDatasetSelect(datasetId: string | null) {
  store.selectedDatasetId = datasetId ?? null
}

// Console resize handlers
function handleConsoleMouseDown(e: MouseEvent | TouchEvent) {
  if (e.cancelable) {
    e.preventDefault()
  }
  isResizingConsole.value = true
  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'ns-resize'
  document.body.style.touchAction = 'none'
}

function handleMouseMove(e: MouseEvent | TouchEvent) {
  if (isResizingConsole.value) {
    let clientY: number
    
    // Check for touches support and existence
    const isTouch = 'touches' in e && (e as TouchEvent).touches.length > 0
    
    if (isTouch) {
      clientY = (e as TouchEvent).touches[0].clientY
    } else if (e instanceof MouseEvent) {
      clientY = e.clientY
    } else {
      return
    }

    const newHeight = window.innerHeight - clientY
    const minHeight = 100
    const maxHeight = window.innerHeight - 200
    store.consoleHeight = Math.min(Math.max(newHeight, minHeight), maxHeight)
  }
}

function handleMouseUp() {
  isResizingConsole.value = false
  document.body.style.userSelect = ''
  document.body.style.cursor = ''
  document.body.style.touchAction = ''
}

// Watchers for UI state consistency
watch(isDatasetNavCollapsed, (val) => {
  store.isRightPanelCollapsed = val
})
</script>

<template>
  <div 
    class="h-[100dvh] flex flex-col bg-slate-50 overflow-hidden"
    @mousemove="handleMouseMove"
    @mouseup="handleMouseUp"
    @touchmove="handleMouseMove"
    @touchend="handleMouseUp"
  >
    <LandingPageOverlay 
      v-if="showLandingPage" 
      @get-started="showLandingPage = false" 
    />
    
    <div 
      class="h-full flex flex-col overflow-hidden transition-all duration-500"
      :class="{ 'blur-sm scale-[0.98]': showLandingPage }"
    >
    <!-- Header -->
    <header class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between flex-shrink-0 shadow-sm z-10">
      <div class="flex items-center gap-3">
        <img src="/icon.svg" alt="VeriFlow Icon" class="w-8 h-8" />
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
      <!-- Left Panel - Upload -->
      <ResizablePanel
        v-if="!isLeftPanelCollapsed"
        side="left"
        :default-width="400"
        :min-width="280"
        :max-width="600"
      >
        <div class="h-full flex flex-col bg-white border-r border-slate-200 overflow-hidden">
          <UploadModule 
            @pdf-upload="handlePdfUpload"
            @collapse-left-panel="isLeftPanelCollapsed = true"
            @load-demo="handleLoadDemo"
            @upload-complete="handleUploadComplete"
            :has-uploaded-files="hasUploadedFiles"
            :is-loading="isLoading"
          />
        </div>
      </ResizablePanel>

      <!-- Collapsed Upload panel -->
      <div v-else class="w-8 bg-slate-50 border-r border-slate-200 flex-shrink-0">
        <button
          @click="isLeftPanelCollapsed = false"
          class="h-full w-full hover:bg-slate-100 transition-colors flex items-center justify-center"
        >
          <span 
            class="text-xs font-medium text-slate-600 whitespace-nowrap" 
            style="writing-mode: vertical-rl; transform: rotate(180deg)"
          >
            Upload Publication
          </span>
        </button>
      </div>

      <!-- Study Design Panel (Conditionally Visible) -->
      <template v-if="isStudyDesignVisible">
        <ResizablePanel
          v-if="!isStudyDesignCollapsed"
          side="left"
          :default-width="400"
          :min-width="280"
          :max-width="600"
        >
          <div class="h-full flex flex-col bg-white border-r border-slate-200 overflow-hidden">
            <StudyDesignModule 
              :selected-assay="selectedAssay"
              :has-uploaded-files="hasUploadedFiles"
              @select-assay="selectedAssay = $event"
              @source-click="handleSourceClick"
              @assemble-click="handleAssembleClick"
              @collapse-left-panel="isStudyDesignCollapsed = true"
              @properties-opened="isConsoleCollapsed = true"
            />
          </div>
        </ResizablePanel>

        <!-- Collapsed Study Design panel -->
        <div v-else class="w-8 bg-slate-50 border-r border-slate-200 flex-shrink-0">
          <button
            @click="isStudyDesignCollapsed = false"
            class="h-full w-full hover:bg-slate-100 transition-colors flex items-center justify-center"
          >
            <span 
              class="text-xs font-medium text-slate-600 whitespace-nowrap" 
              style="writing-mode: vertical-rl; transform: rotate(180deg)"
            >
              Review Study Design
            </span>
          </button>
        </div>
      </template>

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
      class="border-t border-slate-200 flex-shrink-0 bg-white relative flex flex-col" 
      :style="{ height: isConsoleCollapsed ? 'auto' : consoleHeight + 'px' }"
    >
      <!-- Resize handle (only visible when expanded) -->
      <div
        v-if="!isConsoleCollapsed"
        @mousedown="handleConsoleMouseDown"
        @touchstart.prevent="handleConsoleMouseDown"
        class="absolute top-0 left-0 right-0 h-4 cursor-ns-resize transition-colors z-20 opacity-0 hover:opacity-100 bg-blue-500 -top-2"
      />
      
      <div class="flex-1 flex flex-col overflow-hidden min-h-0" :style="{ paddingTop: isConsoleCollapsed ? '0' : '4px' }">
        <!-- Header -->
        <div v-if="!isConsoleCollapsed" class="px-4 py-2 flex items-center justify-between flex-shrink-0">
          <div class="flex items-center gap-2">
            <button
              @click="isConsoleCollapsed = true"
              class="text-slate-400 hover:text-slate-600 transition-colors"
            >
              <ChevronDown class="w-4 h-4" />
            </button>
            <span class="text-sm font-medium text-slate-700">Console</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="flex items-center gap-1">
              <div class="w-2 h-2 rounded-full bg-green-500"></div>
              <span class="text-xs text-slate-500">All agents active</span>
            </div>
          </div>
        </div>
        <div v-else class="h-8 flex-shrink-0 bg-slate-50">
           <button
            @click="isConsoleCollapsed = false"
            class="w-full h-full hover:bg-slate-100 transition-colors flex items-center justify-center gap-2"
          >
            <ChevronUp class="w-4 h-4 text-slate-600" />
            <span class="text-xs font-medium text-slate-600">Console</span>
          </button>
        </div>

        <!-- Content (Messages) -->
        <div v-show="!isConsoleCollapsed" class="flex-1 overflow-hidden">
          <ConsoleModule />
        </div>
      </div>

      <!-- Input (Always rendered, preserving focus) -->
      <ConsoleInput />
    </div>
    </div>
  </div>
</template>
