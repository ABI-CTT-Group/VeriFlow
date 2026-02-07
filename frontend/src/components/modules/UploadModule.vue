<script setup lang="ts">
/**
 * UploadModule.vue
 * Ported from: planning/UI/src/components/UploadModule.tsx
 * 
 * Drag-and-drop file upload with expand/collapse functionality.
 * Stage 6: Added "Load Demo" button for MAMA-MIA example.
 */
import { ref, computed, watch } from 'vue'
import { Upload, File, X, ChevronDown, ChevronRight, ChevronLeft, Loader2, Beaker, Plus } from 'lucide-vue-next'
import { endpoints } from '../../services/api'
import { useWorkflowStore } from '../../stores/workflow'
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
}>()

const store = useWorkflowStore()
const files = ref<string[]>([])
const isDragging = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
// Start collapsed if files have already been uploaded
const isExpanded = ref(!props.hasUploadedFiles)

// Additional Info Modal Logic
const showInfoModal = ref(false)
const previewPdfUrl = ref('')
const isDemoMode = ref(false)
const additionalInfoInput = ref('') // store input if needed, though modal handles its own state mostly

// Watch for external updates to files (e.g. loading demo)
watch(() => props.hasUploadedFiles, (hasFiles) => {
  if (hasFiles) {
    isExpanded.value = false
  }
})

const fileCountText = computed(() => {
  if (files.value.length > 0) {
    return `${files.value.length} file${files.value.length > 1 ? 's' : ''} uploaded`
  }
  return 'Upload a scientific paper (PDF)'
})

function handleDrop(e: DragEvent) {
  e.preventDefault()
  setIsDragging(false)
  
  if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
      const droppedFiles = Array.from(e.dataTransfer.files)
      const fileNames = droppedFiles.map(f => f.name)
      files.value.push(...fileNames)
      
      const pdfFile = droppedFiles.find(f => f.name.toLowerCase().endsWith('.pdf'))
      if (pdfFile) {
          const objectUrl = URL.createObjectURL(pdfFile)
          previewPdfUrl.value = objectUrl
          emit('pdfUpload', pdfFile.name)
          
           // Auto-collapse and show modal after PDF upload
          isExpanded.value = false
          isDemoMode.value = false
          showInfoModal.value = true
      }
  } else {
      // Fallback for mock/testing if needed
      const mockPdf = 'breast_cancer_segmentation.pdf'
      files.value.push(mockPdf)
      emit('pdfUpload', mockPdf)
      isExpanded.value = false
      setTimeout(() => { showInfoModal.value = true }, 500)
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

function handleFileInput(e: Event) {
  const target = e.target as HTMLInputElement
  const uploadedFiles = target.files
  if (uploadedFiles && uploadedFiles.length > 0) {
    const fileList = Array.from(uploadedFiles)
    const fileNames = fileList.map(f => f.name)
    files.value.push(...fileNames)
    
    // Find and notify about PDF
    const pdfFile = fileList.find(f => f.name.toLowerCase().endsWith('.pdf'))
    if (pdfFile) {
      const objectUrl = URL.createObjectURL(pdfFile)
      previewPdfUrl.value = objectUrl
      emit('pdfUpload', pdfFile.name)
      
      // Auto-open modal after PDF upload
      isDemoMode.value = false
      showInfoModal.value = true
    }
    
    // Auto-collapse after file upload
    isExpanded.value = false
  }
}

function handleLoadDemo() {
  // Use the exact path requested by the user
  previewPdfUrl.value = '/A large-scale multicenter breast cancer DCE-MRI benchmark dataset with expert segmentations.pdf'
  isDemoMode.value = true
  showInfoModal.value = true
}

async function handleModalSubmit(info: string) {
  if (isDemoMode.value) {
    emit('loadDemo')
    showInfoModal.value = false
    return
  }

  if (!store.uploadId) {
    console.warn("No upload ID available to attach info")
    // Use timeout to simulate "waiting for backend to give ID" or just proceed if strictly separate
    // For now, assume ID might be there or this is a "best effort"
  }

  // If we have an ID, send it. If not, maybe we should queue it? 
  // For this Refactor, I'll keep existing logic: try to send if ID exists.
  if (store.uploadId) {
      try {
        await endpoints.sendAdditionalInfo(store.uploadId, info)
        console.log("Additional info submitted")
      } catch (error) {
        console.error("Failed to submit additional info", error)
      }
  } else {
      console.warn("Skipping additional info submission: No uploadId")
  }
  
  showInfoModal.value = false
}

function handleModalSkip() {
  if (isDemoMode.value) {
    emit('loadDemo')
  }
  showInfoModal.value = false
}

function removeFile(index: number) {
  files.value.splice(index, 1)
  
  // Update PDF if removed
  const pdfFile = files.value.find(f => f.endsWith('.pdf'))
  emit('pdfUpload', pdfFile || '')
}
</script>

<template>
  <div class="border-b border-slate-200 bg-white flex-shrink-0">
    <div class="flex items-center">
      <!-- Collapse left panel button -->
      <button
        @click="emit('collapseLeftPanel')"
        class="px-2 py-3 text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-colors border-r border-slate-200"
      >
        <ChevronLeft class="w-4 h-4" />
      </button>
      
      <!-- Expand/collapse toggle -->
      <button
        @click="isExpanded = !isExpanded"
        :class="[
          'flex-1 flex items-center justify-between px-4 py-3 hover:bg-slate-50 transition-colors',
          isExpanded ? 'border-b border-slate-200' : ''
        ]"
      >
        <div class="flex items-center gap-2 flex-1">
          <div class="text-left">
            <span class="text-sm font-medium text-slate-700">1. Upload Publication</span>
            <p class="text-xs text-slate-400">{{ fileCountText }}</p>
          </div>
        </div>
        <ChevronDown v-if="isExpanded" class="w-4 h-4 text-slate-400" />
        <ChevronRight v-else class="w-4 h-4 text-slate-400" />
      </button>
    </div>
    
    <!-- Expanded content -->
    <div v-if="isExpanded" class="p-4 space-y-4">
      <!-- Drop zone -->
      <div
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
      <div class="flex items-center gap-3">
        <div class="flex-1 border-t border-slate-200"></div>
        <span class="text-xs text-slate-400">or</span>
        <div class="flex-1 border-t border-slate-200"></div>
      </div>

      <!-- Load Demo Button -->
      <button
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

  <AdditionalInfoModal
    :is-open="showInfoModal"
    :pdf-url="previewPdfUrl"
    :is-demo-mode="isDemoMode"
    @close="showInfoModal = false"
    @submit="handleModalSubmit"
    @skip="handleModalSkip"
  />
</template>
