<script setup lang="ts">
/**
 * UploadModule.vue
 * Ported from: planning/UI/src/components/UploadModule.tsx
 * 
 * Drag-and-drop file upload with expand/collapse functionality.
 * Stage 6: Added "Load Demo" button for MAMA-MIA example.
 */
import { ref, computed, watch } from 'vue'
import { Upload, File, X, ChevronDown, ChevronRight, ChevronLeft, Loader2, Beaker, FileText, Plus } from 'lucide-vue-next'
import { endpoints } from '../../services/api'
import { useWorkflowStore } from '../../stores/workflow'

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
const additionalInfo = ref('')

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
  // Mock file handling
  const mockPdf = 'breast_cancer_segmentation.pdf'
  files.value.push(mockPdf)
  emit('pdfUpload', mockPdf)
  // Auto-collapse and show modal after PDF upload
  isExpanded.value = false
  setTimeout(() => { showInfoModal.value = true }, 500)
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
      // Auto-open modal after PDF upload
      setTimeout(() => { showInfoModal.value = true }, 500)
    }
    
    // Auto-collapse after file upload
    isExpanded.value = false
  }
}

async function handleAdditionalInfoSubmit() {
  if (!store.uploadId) {
    console.warn("No upload ID available to attach info")
    showInfoModal.value = false
    return
  }

  try {
    await endpoints.sendAdditionalInfo(store.uploadId, additionalInfo.value)
    console.log("Additional info submitted")
  } catch (error) {
    console.error("Failed to submit additional info", error)
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



    <!-- Additional Info Modal -->
    <template v-if="showInfoModal">
      <!-- Backdrop -->
      <div 
        class="fixed inset-0 z-[60] bg-black/50 backdrop-blur-sm flex items-center justify-center p-4"
        @click="showInfoModal = false"
      >
        <!-- Card Panel -->
        <div 
          class="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden relative"
          @click.stop
        >
          <!-- Header -->
          <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
            <h3 class="font-semibold text-slate-900 flex items-center gap-2">
              <FileText class="w-5 h-5 text-blue-600" />
              Add More Information (Optional)
            </h3>
            <button 
              @click="showInfoModal = false"
              class="text-slate-400 hover:text-slate-600 transition-colors p-1 rounded-full hover:bg-slate-100"
            >
              <X class="w-5 h-5" />
            </button>
          </div>

          <!-- Body -->
          <div class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">
                Additional Context
              </label>
              <textarea
                v-model="additionalInfo"
                rows="4"
                placeholder="Provide additional guidance to VeriFlow e.g. “Only interested in the workflow that performs inference using a pre-trained network” or “The path to example data can be found here …”."
                class="w-full px-4 py-3 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-shadow resize-none"
              ></textarea>
            </div>

            <!-- Description -->
            <div class="bg-blue-50 border border-blue-100 rounded-lg p-3">
              <p class="text-xs text-blue-800 leading-relaxed">
                This information will be used by our AI Agents to better understand your specific requirements and generate more accurate workflows.
              </p>
            </div>
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 bg-slate-50 border-t border-slate-100 flex justify-end gap-3">
            <button
              @click="showInfoModal = false"
              class="px-4 py-2 text-sm font-medium text-slate-700 hover:text-slate-900 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
            >
              Skip
            </button>
            <button
              @click="handleAdditionalInfoSubmit"
              class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 shadow-sm shadow-blue-200 transition-all active:scale-95"
            >
              Finished
            </button>
          </div>
        </div>
      </div>
    </template>
</template>
