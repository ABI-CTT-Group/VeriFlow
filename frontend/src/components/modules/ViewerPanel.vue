<script setup lang="ts">
/**
 * ViewerPanel.vue
 * Ported from: planning/UI/src/components/ViewerPanel.tsx
 * 
 * PDF document viewer with extraction annotations.
 */
import { ref, watch, computed } from 'vue'
import { FileText, X } from 'lucide-vue-next'

interface Annotation {
  page: number
  x: number
  y: number
  width: number
  height: number
  color: string
  propertyId: string
  label: string
}

interface Props {
  pdfUrl?: string
  activePropertyId?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const currentPage = ref(1)

// Define annotations for different extracted properties
const extractionAnnotations: Annotation[] = [
  { page: 1, x: 10, y: 15, width: 80, height: 8, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'paper-title', label: 'Paper Title' },
  { page: 1, x: 10, y: 28, width: 60, height: 5, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'paper-authors', label: 'Authors' },
  { page: 1, x: 10, y: 38, width: 20, height: 4, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'paper-year', label: 'Year' },
  { page: 2, x: 10, y: 20, width: 80, height: 15, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'inv-title', label: 'Investigation Title' },
  { page: 2, x: 10, y: 38, width: 80, height: 18, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'inv-description', label: 'Investigation Description' },
  { page: 3, x: 10, y: 25, width: 70, height: 8, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'study-title', label: 'Study Title' },
  { page: 3, x: 10, y: 55, width: 35, height: 5, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'study-subjects', label: 'Number of Subjects' },
  { page: 4, x: 10, y: 30, width: 50, height: 8, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'assay-name', label: 'Assay Name' },
  { page: 4, x: 10, y: 55, width: 65, height: 5, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'step-step-1', label: 'Step 1: Data Acquisition' },
  { page: 4, x: 10, y: 65, width: 70, height: 5, color: 'rgba(234, 179, 8, 0.3)', propertyId: 'step-step-2', label: 'Step 2: DICOM to NIfTI' },
]

const sections: Record<string, { title: string; content: string; location: string }> = {
  'paper-title': {
    title: 'Paper Title',
    content: 'Breast Cancer Segmentation Using Deep Learning',
    location: 'Page 1, Title Section'
  },
  'paper-authors': {
    title: 'Authors',
    content: 'Smith, J., Johnson, A., Williams, B., Brown, C.',
    location: 'Page 1, Authors Section'
  },
  'paper-year': {
    title: 'Publication Year',
    content: '2023',
    location: 'Page 1, Header'
  },
  'inv-title': {
    title: 'Investigation Title',
    content: 'Automated Tumor Detection Investigation',
    location: 'Page 2, Introduction'
  },
  'study-title': {
    title: 'Study Title',
    content: 'MRI-based Segmentation Study',
    location: 'Page 3, Study Design'
  },
  'study-subjects': {
    title: 'Number of Subjects',
    content: '384 subjects',
    location: 'Page 3, Participants'
  },
  'assay-name': {
    title: 'Assay Name',
    content: 'U-Net Training Assay',
    location: 'Page 4, Training Protocol'
  }
}

const highlightedSection = computed(() => sections[props.activePropertyId || ''] || null)

const activeAnnotation = computed(() => 
  extractionAnnotations.find(a => a.propertyId === props.activePropertyId)
)

const pageAnnotations = computed(() => 
  extractionAnnotations.filter(a => a.page === currentPage.value)
)

// Auto-navigate to page containing active annotation
watch(() => props.activePropertyId, () => {
  if (activeAnnotation.value && currentPage.value !== activeAnnotation.value.page) {
    currentPage.value = activeAnnotation.value.page
  }
})
</script>

<template>
  <div v-if="!pdfUrl" class="h-full flex items-center justify-center bg-slate-50">
    <div class="text-center text-slate-400">
      <FileText class="w-12 h-12 mx-auto mb-3 opacity-50" />
      <p class="text-sm">No document selected</p>
      <p class="text-xs mt-1">Click "Source" on any property to view</p>
    </div>
  </div>

  <div v-else class="h-full flex flex-col bg-white">
    <!-- Header -->
    <div class="px-4 py-3 border-b border-slate-200 flex items-center justify-between flex-shrink-0">
      <div class="flex items-center gap-2">
        <FileText class="w-4 h-4 text-slate-600" />
        <div>
          <span class="text-sm font-medium text-slate-700">Document Viewer</span>
          <p v-if="highlightedSection" class="text-xs text-slate-500">
            {{ highlightedSection.location }}
          </p>
        </div>
      </div>
      <button @click="emit('close')" class="text-slate-400 hover:text-slate-600">
        <X class="w-4 h-4" />
      </button>
    </div>

    <!-- Extraction Info Banner -->
    <div v-if="highlightedSection" class="px-4 py-2 bg-blue-50 border-b border-blue-200 flex-shrink-0">
      <div class="flex items-start gap-2">
        <div class="w-2 h-2 rounded-full bg-blue-600 mt-1.5 flex-shrink-0"></div>
        <div class="flex-1 min-w-0">
          <p class="text-xs font-medium text-blue-900">Scholar extracted from {{ highlightedSection.location }}:</p>
          <p class="text-xs text-blue-700 mt-0.5 italic">"{{ highlightedSection.content }}"</p>
        </div>
      </div>
    </div>

    <!-- PDF Viewer Area -->
    <div class="flex-1 overflow-auto bg-slate-100 p-6">
      <div class="relative bg-white border border-slate-300 mx-auto" style="width: 612px; height: 792px;">
        <!-- Mock PDF Content -->
        <div class="p-12 text-sm leading-relaxed text-slate-700">
          <!-- Page 1 -->
          <template v-if="currentPage === 1">
            <h1 class="text-3xl font-bold mb-6 text-slate-900">
              Breast Cancer Segmentation Using Deep Learning
            </h1>
            <p class="text-base text-slate-600 mb-2">
              Smith, J., Johnson, A., Williams, B., Brown, C.
            </p>
            <p class="text-sm text-slate-500">Department of Medical Imaging, University Hospital</p>
            <p class="text-sm text-slate-600 mt-4">Published: 2023</p>
            <h2 class="text-xl font-bold mb-3 text-slate-900 mt-8">Abstract</h2>
            <p class="text-justify">
              This study presents a novel approach to automated breast cancer segmentation
              using deep learning techniques on DCE-MRI scans. Early detection and accurate 
              segmentation of tumors is crucial for effective treatment planning.
            </p>
          </template>

          <!-- Page 2 -->
          <template v-if="currentPage === 2">
            <h2 class="text-xl font-bold mb-4 text-slate-900">Introduction</h2>
            <p class="mb-4 text-justify">
              This investigation focuses on automated tumor detection using deep learning methods.
              The primary objective is to develop a reliable system for breast tumor detection 
              and segmentation in DCE-MRI images.
            </p>
            <p class="mb-4 text-justify">
              Investigation of automated deep learning methods for breast tumor detection and 
              segmentation in DCE-MRI images represents a critical advancement in medical imaging 
              analysis.
            </p>
            <p class="text-sm text-slate-600 mt-4">Study Timeline: January 2023 - June 2023</p>
          </template>

          <!-- Page 3 -->
          <template v-if="currentPage === 3">
            <h2 class="text-xl font-bold mb-4 text-slate-900">Methods</h2>
            <h3 class="text-lg font-semibold mb-2 text-slate-800">MRI-based Segmentation Study</h3>
            <p class="text-justify mb-6">
              We conducted a comprehensive study of U-Net based segmentation on breast MRI scans.
              The methodology involved multiple stages of image processing, data augmentation,
              and model training to ensure robust performance.
            </p>
            <h3 class="text-base font-semibold mb-2 text-slate-800">Participants</h3>
            <p class="text-justify">
              We collected DCE-MRI scans from 384 subjects diagnosed with breast cancer.
              All images were acquired using a 3T MRI scanner with standardized T1-weighted 
              sequences following institutional protocols.
            </p>
          </template>

          <!-- Page 4 -->
          <template v-if="currentPage === 4">
            <h2 class="text-xl font-bold mb-4 text-slate-900">Training Protocol</h2>
            <h3 class="text-lg font-semibold mb-2 text-slate-800">U-Net Training Assay</h3>
            <p class="text-justify mb-4">
              The segmentation model was trained using a U-Net architecture with pretrained 
              nnU-Net weights. The training protocol included data augmentation techniques such 
              as random rotations, elastic deformations, and intensity variations.
            </p>
            <h3 class="text-base font-semibold mb-2 text-slate-800">Data Processing</h3>
            <p class="text-justify">
              DICOM images were converted to NIfTI format using the dcm2niix tool.
              Preprocessing steps included intensity normalization using Z-score standardization
              and bias field correction using the N4ITK algorithm.
            </p>
          </template>
        </div>

        <!-- Annotation Overlays -->
        <div
          v-for="(annotation, idx) in pageAnnotations"
          :key="idx"
          :class="[
            'absolute pointer-events-none transition-all duration-300',
            annotation.propertyId === activePropertyId ? 'opacity-100 ring-2 ring-blue-500' : 'opacity-0'
          ]"
          :style="{
            left: annotation.x + '%',
            top: annotation.y + '%',
            width: annotation.width + '%',
            height: annotation.height + '%',
            backgroundColor: annotation.color,
            borderLeft: annotation.propertyId === activePropertyId ? '4px solid #3b82f6' : 'none'
          }"
        >
          <div
            v-if="annotation.propertyId === activePropertyId"
            class="absolute -top-6 left-0 bg-blue-600 text-white text-xs px-2 py-1 rounded whitespace-nowrap shadow-lg"
          >
            {{ annotation.label }}
          </div>
        </div>
      </div>
    </div>

    <!-- Page Navigation -->
    <div class="px-4 py-3 border-t border-slate-200 flex items-center justify-between flex-shrink-0 bg-white">
      <button
        @click="currentPage = Math.max(1, currentPage - 1)"
        :disabled="currentPage === 1"
        class="px-3 py-1 text-xs border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Previous
      </button>
      <span class="text-xs text-slate-600">
        Page {{ currentPage }} of 4
      </span>
      <button
        @click="currentPage = Math.min(4, currentPage + 1)"
        :disabled="currentPage === 4"
        class="px-3 py-1 text-xs border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Next
      </button>
    </div>
  </div>
</template>
