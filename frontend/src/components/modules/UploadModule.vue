<script setup lang="ts">
/**
 * UploadModule.vue
 * Ported from: planning/UI/src/components/UploadModule.tsx
 * 
 * Drag-and-drop file upload with expand/collapse functionality.
 * Stage 6: Added "Load Demo" button for MAMA-MIA example.
 */
import { ref, computed } from 'vue'
import { Upload, File, X, ChevronLeft, Loader2, Beaker, Plus, Info } from 'lucide-vue-next'
import { endpoints } from '../../services/api'
import { useWorkflowStore } from '../../stores/workflow'
import { useConsoleStore } from '../../stores/console'
import AdditionalInfoModal from './AdditionalInfoModal.vue'

interface Props {
  hasUploadedFiles?: boolean
  isLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  hasUploadedFiles: false,
  isLoading: false,
})

const emit = defineEmits<{
  pdfUpload: [pdfUrl: string]
  collapseLeftPanel: []
  loadDemo: []
  uploadComplete: []
}>()

const store = useWorkflowStore()
const files = ref<string[]>([])
const isDragging = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)

// Additional Info Modal Logic
const showInfoModal = ref(false)
const previewPdfUrl = ref('')
const isDemoMode = ref(false)
const uploadedPdfPath = ref('')
const uploadedRepoPath = ref('')
const isUploading = ref(false)

const fileCountText = computed(() => {
  if (files.value.length > 0) {
    return `${files.value.length} file${files.value.length > 1 ? 's' : ''} uploaded`
  }
  return 'Upload a scientific paper (PDF)'
})

async function handleDrop(e: DragEvent) {
  e.preventDefault()
  setIsDragging(false)
  
  if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
      const droppedFiles = Array.from(e.dataTransfer.files)
      const fileNames = droppedFiles.map(f => f.name)
      files.value.push(...fileNames)
      
      const pdfFile = droppedFiles.find(f => f.name.toLowerCase().endsWith('.pdf'))
      if (pdfFile) {
          await processPdfUpload(pdfFile)
      }
  }
}

function handleDragOver(e: DragEvent) {
  e.preventDefault()
  setIsDragging(true)
}

function setIsDragging(value: boolean) {
  isDragging.value = value
}

function handleBrowseClick() {
  fileInputRef.value?.click()
}

async function handleFileInput(e: Event) {
  const target = e.target as HTMLInputElement
  const uploadedFiles = target.files
  if (uploadedFiles && uploadedFiles.length > 0) {
    const fileList = Array.from(uploadedFiles)
    const fileNames = fileList.map(f => f.name)
    files.value.push(...fileNames)
    
    // Find and notify about PDF
    const pdfFile = fileList.find(f => f.name.toLowerCase().endsWith('.pdf'))
    if (pdfFile) {
      await processPdfUpload(pdfFile)
    }
    
    // Auto-collapse after file upload

  }
}

async function processPdfUpload(file: File) {
    const objectUrl = URL.createObjectURL(file)
    previewPdfUrl.value = objectUrl
    
    // 1. Generate ID
    const pdfId = crypto.randomUUID()
    
    try {
        isUploading.value = true
        // 2. Upload to backend
        const response = await endpoints.uploadPublicationWithId(file, pdfId)
        
        // 3. Store paths
        if (response.data.pdf_path && response.data.folder_path) {
            uploadedPdfPath.value = response.data.pdf_path
            uploadedRepoPath.value = response.data.folder_path
            // Store upload_id in the store for subsequent calls (e.g. additional info)
            store.uploadId = response.data.upload_id
            emit('pdfUpload', file.name)
        }
        
        isDemoMode.value = false
        showInfoModal.value = true
    } catch (error: any) {
        console.error("Upload failed", error)
        if (error.response && error.response.status === 413) {
            alert("File is too large. Please upload a smaller file (max 2GB).")
        } else {
            alert("Upload failed: " + (error.message || "Unknown error"))
        }
    } finally {
        isUploading.value = false
    }
}

function handleLoadDemo() {
  // Use the exact path requested by the user
  previewPdfUrl.value = '/A large-scale multicenter breast cancer DCE-MRI benchmark dataset with expert segmentations.pdf'
  isDemoMode.value = true
  showInfoModal.value = true
}

async function handleModalSubmit(info: string) {
  // Handle Demo Mode
  if (isDemoMode.value) {
    emit('loadDemo')
    showInfoModal.value = false
    
    // Expand console automatically
    if (store.isConsoleCollapsed) {
      store.isConsoleCollapsed = false
    }
    emit('uploadComplete')
    return
  }

  if (!store.uploadId) {
    console.warn("No upload ID available to attach info")
    // Use timeout to simulate "waiting for backend to give ID" or just proceed if strictly separate
    // For now, assume ID might be there or this is a "best effort"
  }

  // If we have an ID, send it. If not, maybe we should queue it? 
  // For this Refactor, I'll keep existing logic: try to send if ID exists.
  
  // Trigger Orchestration
  if (!isDemoMode.value && uploadedPdfPath.value && uploadedRepoPath.value) {
      // Don't await orchestration - let it run in background to allow UI transition
      console.log("Starting orchestration in background...")
      
      // Emit immediately to switch UI
      emit('uploadComplete')
      
      // Open Console Panel
      store.isConsoleCollapsed = false

      // Add start message to console
      const consoleStore = useConsoleStore()
      consoleStore.addSystemMessage("Starting orchestration in background...")
      
      // Set loading state
      store.isLoading = true
      store.loadingMessage = "Analyzing publication and generating study design..."
      
      // Ensure WebSocket is connected for real-time updates
      try {
        await store.initWebSocket()
      } catch (wsError) {
        console.error("Failed to initialize WebSocket:", wsError)
        // Proceed anyway, but real-time updates might fail
      }

      const clientId = store.clientId || undefined
      
      endpoints.orchestrateWorkflow(
          uploadedPdfPath.value, 
          uploadedRepoPath.value,
          info, // Pass additional info as userContext
          clientId 
      ).then(async response => {
          console.log("Orchestration Started:", response.data)
          
          if (response.data.status === 'started' && (response.data.result as any)?.run_id) {
              const runId = (response.data.result as any).run_id
              store.currentRunId = runId // Fix: Update store with runId
              
              const consoleStore = useConsoleStore()
              consoleStore.addSystemMessage(`Orchestration started (Run ID: ${runId}). Waiting for Scholar...`)
              
              // Poll for Scholar Result
              const pollForArtifact = async (attempt = 1) => {
                  if (attempt > 60) {
                       throw new Error("Timeout waiting for Scholar results")
                  }
                  
                  try {
                      if (attempt <= 2) {
                          consoleStore.addSystemMessage(`Checking for Scholar results... (Attempt ${attempt})`)
                      }
                      const artifactRes = await endpoints.getArtifact(runId, 'scholar')
                      
                      if (artifactRes.status === 200 && artifactRes.data) {
                          consoleStore.addSystemMessage("Scholar results received.")
                          
                          const scholarData = artifactRes.data
                          
                          // Create pseudo-result to match old structure
                          const pseudoResult = {
                              isa_json: scholarData.final_output || scholarData.isa_json,
                              generated_code: {}
                          }
                          
                          if (pseudoResult.isa_json) {
                               console.log("Setting hierarchy from orchestration result")
                               store.setHierarchyFromOrchestration(pseudoResult.isa_json)
                          }
                          return // Success
                      }
                  } catch (e: any) {
                      if (e.response && e.response.status === 404) {
                          // Not ready yet, wait and retry
                          await new Promise(resolve => setTimeout(resolve, 5000))
                          await pollForArtifact(attempt + 1)
                      } else {
                          throw e // Critical error
                      }
                  }
              }
              
              await pollForArtifact()
          } else {
              // Fallback for immediate completion (unlikely)
             if (response.data.status === 'completed' && response.data.result) {
                  const res = response.data.result
                  if (res.isa_json) {
                       console.log("Setting hierarchy from orchestration result")
                       store.setHierarchyFromOrchestration(res.isa_json)
                  }
             } else {
                 throw new Error("Failed to start orchestration")
             }
          }
      }).catch(error => {
          console.error("Orchestration failed", error)
          store.error = "Orchestration failed: " + (error.message || "Unknown error")
          
          const consoleStore = useConsoleStore()
          consoleStore.addSystemMessage(`Orchestration failed: ${error.message}`)
      }).finally(() => {
          store.isLoading = false
          store.loadingMessage = null
      })
  }
  

  
  showInfoModal.value = false
  
  // Expand console automatically
  if (store.isConsoleCollapsed) {
    store.isConsoleCollapsed = false
  }
}

function handleModalSkip() {
  if (isDemoMode.value) {
    emit('loadDemo')
  }
  showInfoModal.value = false
  
  // Expand console automatically
  if (store.isConsoleCollapsed) {
    store.isConsoleCollapsed = false
  }
}

function removeFile(index: number) {
  files.value.splice(index, 1)
  
  // Update PDF if removed
  const pdfFile = files.value.find(f => f.endsWith('.pdf'))
  emit('pdfUpload', pdfFile || '')
}
</script>

<template>
  <div class="h-full flex flex-col border-b border-slate-200 bg-white" data-tour="upload-panel">
    <div class="flex-shrink-0 flex items-center">
      <!-- Collapse left panel button -->
      <button
        @click="emit('collapseLeftPanel')"
        class="px-2 py-3 text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-colors border-r border-slate-200"
      >
        <ChevronLeft class="w-4 h-4" />
      </button>
      

      <!-- Static Header -->
      <div class="flex-1 flex items-center justify-between px-4 py-3 bg-slate-50 border-b border-slate-200">
        <div class="flex items-center gap-2 flex-1">
          <div class="text-left">
            <span class="text-sm font-medium text-slate-700">1. Upload Publication</span>
            <p class="text-xs text-slate-400">{{ fileCountText }}</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Expanded content -->
    <div class="flex-1 overflow-y-auto p-6 md:p-8 flex flex-col items-center justify-center">
      <div class="w-full max-w-lg space-y-6 2xl:space-y-12">
      <!-- Testing Hint -->
      <div class="p-3 bg-blue-50 border border-blue-200 rounded-md flex items-start gap-2">
        <Info class="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
        <p class="text-xs text-blue-700 leading-relaxed">
          <span class="font-semibold block mb-0.5">Need a testing example?</span>
          You can get the example PDF from this 
          <a href="https://www.nature.com/articles/s41597-025-04707-4" target="_blank" class="font-medium underline hover:text-blue-800">
            Nature article
          </a>
          and upload it in the box below to start the analysis.
        </p>
      </div>

      <!-- Drop zone -->
      <div
        data-tour="pdf-upload-zone"
        :class="[
          'border-2 border-dashed rounded-lg p-6 text-center transition-colors',
          isDragging ? 'border-blue-500 bg-blue-50' : 'border-slate-300'
        ]"
        @dragover="handleDragOver"
        @dragleave="setIsDragging(false)"
        @drop="handleDrop"
      >
        <Upload class="w-8 h-8 mx-auto text-slate-400 mb-2" />
        <p class="text-sm text-slate-600">
          Drop files here or 
          <span class="text-blue-600 cursor-pointer" @click="handleBrowseClick">browse</span>
        </p>
        <p class="text-xs text-slate-400 mt-1">PDF, ZIP, or code repositories</p>
      </div>

      <!-- Divider with "or" -->
      <div class="flex items-center gap-4">
        <div class="flex-1 border-t border-slate-300"></div>
        <span class="text-sm font-medium text-slate-500">OR</span>
        <div class="flex-1 border-t border-slate-300"></div>
      </div>

      <!-- Load Demo Button -->
      <button
        data-tour="load-demo"
        @click="handleLoadDemo"
        :disabled="props.isLoading"
        :class="[
          'w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all',
          props.isLoading 
            ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
            : 'bg-gradient-to-r from-purple-500 to-indigo-500 text-white hover:from-purple-600 hover:to-indigo-600 shadow-md hover:shadow-lg'
        ]"
      >
        <Loader2 v-if="props.isLoading" class="w-4 h-4 animate-spin" />
        <Beaker v-else class="w-4 h-4" />
        <span>{{ props.isLoading ? 'Loading...' : 'Load MAMA-MIA Demo' }}</span>
      </button>
      <p class="text-xs text-slate-400 text-center">Pre-loaded MRI segmentation example</p>

      <!-- Uploaded files list -->
      <div v-if="files.length > 0" class="space-y-4">
        <div>
          <p class="text-xs text-slate-500 mb-2">Uploaded Files</p>
          <div
            v-for="(file, index) in files"
            :key="index"
            class="flex items-center justify-between p-2 bg-slate-50 rounded border border-slate-200"
          >
            <div class="flex items-center gap-2">
              <File class="w-4 h-4 text-slate-400" />
              <span class="text-sm text-slate-700">{{ file }}</span>
            </div>
            <button
              @click="removeFile(index)"
              class="text-slate-400 hover:text-slate-600"
            >
              <X class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Add info button (only visible when files exist) -->
        <button
          @click="showInfoModal = true"
          class="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-blue-600 border border-blue-200 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
        >
          <Plus class="w-4 h-4" />
          <span>Add additional information</span>
        </button>
      </div>
      
      <!-- Hidden file input -->
      <input
        ref="fileInputRef"
        type="file"
        accept=".pdf,application/pdf"
        @change="handleFileInput"
        class="hidden"
      />
      </div>
    </div>
  </div>

  <AdditionalInfoModal
    :is-open="showInfoModal"
    :pdf-url="previewPdfUrl"
    :is-demo-mode="isDemoMode"
    @close="showInfoModal = false"
    @submit="handleModalSubmit"
    @skip="handleModalSkip"
  />
</template>
