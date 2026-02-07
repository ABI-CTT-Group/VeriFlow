<script setup lang="ts">
import { ref, watch } from 'vue'
import { FileText, X } from 'lucide-vue-next'

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

// Initialize or reset input based on demo mode when modal opens
watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    if (props.isDemoMode) {
      additionalInfo.value = 'The MAMA-MIA demo additional inputs have been configured.'
    } else {
      additionalInfo.value = ''
    }
  }
})

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
        <button 
          @click="handleClose"
          class="text-slate-400 hover:text-slate-600 transition-colors p-1 rounded-full hover:bg-slate-100"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Content - Split View -->
      <div class="flex-1 flex overflow-hidden">
        
        <!-- Left Panel: PDF Preview -->
        <div class="w-1/2 bg-slate-100 border-r border-slate-200 flex flex-col">
          <div v-if="pdfUrl" class="flex-1 w-full h-full">
            <iframe :src="pdfUrl" class="w-full h-full border-none"></iframe>
          </div>
          <div v-else class="flex-1 flex items-center justify-center text-slate-400">
            <p>No PDF available for preview</p>
          </div>
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
