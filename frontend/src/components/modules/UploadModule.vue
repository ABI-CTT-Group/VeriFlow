<script setup lang="ts">
/**
 * UploadModule.vue
 * Ported from: planning/UI/src/components/UploadModule.tsx
 * 
 * Drag-and-drop file upload with expand/collapse functionality.
 * Stage 6: Added "Load Demo" button for MAMA-MIA example.
 */
import { ref, computed } from 'vue'
import { Upload, File, X, ChevronDown, ChevronRight, ChevronLeft, Loader2, Beaker } from 'lucide-vue-next'

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

const files = ref<string[]>([])
const isDragging = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
// Start collapsed if files have already been uploaded
const isExpanded = ref(!props.hasUploadedFiles)

const fileCountText = computed(() => {
  if (files.value.length > 0) {
    return `${files.value.length} file${files.value.length > 1 ? 's' : ''} uploaded`
  }
  return 'Upload a scientific paper (PDF)'
})

function handleDrop(e: DragEvent) {
  e.preventDefault()
  setIsDragging(false)
  // Mock file handling
  const mockPdf = 'breast_cancer_segmentation.pdf'
  files.value.push(mockPdf)
  emit('pdfUpload', mockPdf)
  // Auto-collapse after PDF upload
  isExpanded.value = false
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
    const fileNames = Array.from(uploadedFiles).map(f => f.name)
    files.value.push(...fileNames)
    
    // Find and notify about PDF
    const pdfFile = fileNames.find(f => f.toLowerCase().endsWith('.pdf'))
    if (pdfFile) {
      emit('pdfUpload', pdfFile)
    }
    
    // Auto-collapse after file upload
    isExpanded.value = false
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
        @click="emit('loadDemo')"
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
      <div v-if="files.length > 0" class="space-y-2">
        <p class="text-xs text-slate-500">Uploaded Files</p>
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
</template>
