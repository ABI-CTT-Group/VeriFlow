<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { FileText, X, ChevronLeft, ChevronRight, Loader2, Monitor, Smartphone } from 'lucide-vue-next'
import VuePdfEmbed from 'vue-pdf-embed'
// Essential: import worker for pdf.js explicitly
import * as pdfjsLib from 'pdfjs-dist'

// Set worker source (using CDN for simplicity and reliability with Vite)
// Alternatively, we could copy the worker file to public assets, but this is a standard pattern
pdfjsLib.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`

interface Props {
  isOpen: boolean
  pdfUrl?: string
  isDemoMode?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isOpen: false,
  pdfUrl: '',
  isDemoMode: false,
})

const emit = defineEmits<{
  close: []
  submit: [value: string]
  skip: []
}>()

const additionalInfo = ref('')

// PDF Viewer State
const pdfPage = ref(1)
const pageCount = ref(0)
const pdfScale = ref(1.0)
const isLoadingPdf = ref(false)
const pdfKey = ref(0) // Force re-render if needed

// Viewer Mode: True = Custom (VuePdf), False = Native (Iframe)
const useCustomViewer = ref(false)

onMounted(() => {
  // Broad detection: If touch capability exists, err on the side of using the Custom Viewer
  // This covers iPads, mobile phones, and hybrid laptops (which usually handle the JS viewer fine)
  const isTouchDevice = navigator.maxTouchPoints > 0 || /iPad|iPhone|iPod|Android/.test(navigator.userAgent)
  useCustomViewer.value = isTouchDevice
})

function toggleViewer() {
  useCustomViewer.value = !useCustomViewer.value
  // Reset PDF state when switching
  pdfPage.value = 1
  pdfScale.value = 1.0
  isLoadingPdf.value = true
  pdfKey.value++
}

// Initialize or reset
watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    // Pre-fill context for both Demo and Upload flows as requested
    additionalInfo.value = `- We are interested in the pre-trained model inference assay for MRI segmentation 
- Interested in the first subject of the Duke University dataset which is located in this location in dicom format: https://github.com/ABI-CTT-Group/VeriFlow/tree/main/examples/raw_dicoms/DUKE_MRI_001 
- Can use the Dicom to nifti library 
- Result of workflow should be segmentation result using the 3D pre-network in nifti format 
- We will use cpu for executing nnunet 
- Here is the path to the pre-trained nnunet mode which is located in the local file system where the python script tools will be run: /app/nnUNet_results`
    // Reset PDF state
    pdfPage.value = 1
    pdfScale.value = 1.0
    isLoadingPdf.value = true
    // Force component refresh
    pdfKey.value++
  }
})

// PDF Handlers
function handlePdfLoaded(doc: any) {
  isLoadingPdf.value = false
  pageCount.value = doc.numPages
}

function handlePdfError(error: any) {
  console.error("PDF Render Error:", error)
  isLoadingPdf.value = false
}


function prevPage() {
  if (pdfPage.value > 1) pdfPage.value--
}

function nextPage() {
  if (pdfPage.value < pageCount.value) pdfPage.value++
}

function handleSubmit() {
  emit('submit', additionalInfo.value)
}

function handleSkip() {
  emit('skip')
}

function handleClose() {
  emit('close')
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-[60] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-6xl h-[85vh] overflow-hidden relative flex flex-col" @click.stop>
      
      <!-- Header -->
      <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50 flex-shrink-0">
        <h3 class="font-semibold text-slate-900 flex items-center gap-2">
          <FileText class="w-5 h-5 text-blue-600" />
          Add More Information (Optional)
        </h3>
        <div class="flex items-center gap-2">
          <!-- Viewer Toggle -->
          <button 
            @click="toggleViewer"
            class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
            title="Switch PDF Viewer Engine"
          >
            <component :is="useCustomViewer ? Smartphone : Monitor" class="w-3.5 h-3.5" />
            <span>{{ useCustomViewer ? 'Web Viewer' : 'Native Viewer' }}</span>
          </button>

          <button 
            @click="handleClose"
            class="text-slate-400 hover:text-slate-600 transition-colors p-1 rounded-full hover:bg-slate-100"
          >
            <X class="w-5 h-5" />
          </button>
        </div>
      </div>

      <!-- Content - Split View -->
      <div class="flex-1 flex overflow-hidden">
        
        <!-- Left Panel: Hybrid PDF Viewer -->
        <div class="w-1/2 bg-slate-100 border-r border-slate-200 flex flex-col relative group">
          
          <!-- Case A: Custom Web Viewer (VuePdfEmbed) - For iOS/Touch/Fallback -->
          <template v-if="useCustomViewer">
            <!-- PDF Toolbar -->
            <div v-if="pdfUrl" class="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 flex items-center gap-2 bg-slate-900/80 backdrop-blur shadow-lg rounded-full px-4 py-2 border border-slate-700 transition-opacity">
              <!-- Navigation -->
              <div class="flex items-center gap-3 text-white">
                <button @click="prevPage" :disabled="pdfPage <= 1" class="touch-manipulation p-1 hover:bg-white/10 rounded disabled:opacity-30 transition-colors">
                  <ChevronLeft class="w-5 h-5 pointer-events-none" />
                </button>
                <span class="select-none text-sm font-medium min-w-[3rem] text-center tabular-nums">
                  {{ pdfPage }} / {{ pageCount || '-' }}
                </span>
                <button @click="nextPage" :disabled="pdfPage >= pageCount" class="touch-manipulation p-1 hover:bg-white/10 rounded disabled:opacity-30 transition-colors">
                  <ChevronRight class="w-5 h-5 pointer-events-none" />
                </button>
              </div>


            </div>

            <!-- Viewer Container -->
            <div class="flex-1 overflow-auto bg-slate-200/50 flex justify-center relative" id="pdf-container">
              <div v-if="isLoadingPdf" class="absolute inset-0 flex items-center justify-center bg-white/50 z-10">
                <Loader2 class="w-8 h-8 text-blue-600 animate-spin" />
              </div>

              <div v-if="pdfUrl" class="shadow-xl" :style="{ width: pdfScale * 100 + '%' }">
                 <VuePdfEmbed
                  :key="pdfKey"
                  :source="pdfUrl"
                  :page="pdfPage"
                  :text-layer="false"
                  :annotation-layer="false"
                  @loaded="handlePdfLoaded"
                  @rendered="isLoadingPdf = false"
                  @error="handlePdfError"
                  class="bg-white w-full transition-transform duration-200"
                />
              </div>
              
              <div v-else class="flex-1 flex items-center justify-center text-slate-400">
                <p>No PDF available for preview</p>
              </div>
            </div>
          </template>

          <!-- Case B: PC/Native Viewer (Iframe) -->
          <template v-else>
             <div v-if="pdfUrl" class="flex-1 w-full h-full">
              <iframe :src="pdfUrl" class="w-full h-full border-none"></iframe>
            </div>
            <div v-else class="flex-1 flex items-center justify-center text-slate-400">
              <p>No PDF available for preview</p>
            </div>
          </template>

        </div>

        <!-- Right Panel: Form -->
        <div class="w-1/2 flex flex-col bg-white">
          <div class="p-8 space-y-6 flex-1 overflow-y-auto">
            
            <div class="space-y-4">
               <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">
                  Additional Context
                </label>
                <textarea
                  v-model="additionalInfo"
                  :disabled="isDemoMode"
                  rows="12"
                  placeholder="Provide additional guidance to VeriFlow e.g. “Only interested in the workflow that performs inference using a pre-trained network” or “The path to example data can be found here …”."
                  class="w-full px-4 py-3 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-shadow resize-none disabled:bg-slate-50 disabled:text-slate-500 disabled:cursor-not-allowed"
                ></textarea>
              </div>

              <!-- Description Box -->
              <div class="bg-blue-50 border border-blue-100 rounded-lg p-4">
                <p class="text-sm text-blue-800 leading-relaxed">
                  This information will be used by our AI Agents to better understand your specific requirements and generate more accurate workflows.
                </p>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="px-8 py-5 bg-slate-50 border-t border-slate-100 flex justify-end gap-3 flex-shrink-0">
            <button
              @click="handleSkip"
              class="px-5 py-2.5 text-sm font-medium text-slate-700 hover:text-slate-900 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
            >
              Skip
            </button>
            <button
              @click="handleSubmit"
              class="px-5 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 shadow-sm shadow-blue-200 transition-all active:scale-95"
            >
              Continue
            </button>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
/* Optional: Hide scrollbar for the PDF container if desirable, 
   but usually vertical scroll is wanted for the page logic if we change to "all pages" mode.
   Here we are using single page mode with internal scrolling if zoomed. */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
