<script setup lang="ts">
/**
 * StudyDesignModule.vue
 * Ported from: planning/UI/src/components/StudyDesignModule.tsx
 * 
 * ISA hierarchy tree viewer with property editing and source citations.
 */
import { ref, watch } from 'vue'
import { 
  FileText, BookOpen, FlaskConical, Layers, 
  ChevronRight, ChevronDown, ChevronLeft, 
  ExternalLink, X, Plus 
} from 'lucide-vue-next'
import ResizablePanel from '../layout/ResizablePanel.vue'

interface Props {
  selectedAssay: string | null
  hasUploadedFiles: boolean
}

interface SelectedItem {
  id: string
  type: 'paper' | 'investigation' | 'study' | 'assay'
  name: string
}

interface WorkflowStep {
  id: string
  description: string
}

const props = withDefaults(defineProps<Props>(), {
  selectedAssay: null,
  hasUploadedFiles: false,
})

const emit = defineEmits<{
  selectAssay: [assayId: string | null]
  sourceClick: [propertyId: string]
  assembleClick: []
  collapseLeftPanel: []
}>()

const selectedItem = ref<SelectedItem | null>(null)
const isExpanded = ref(props.hasUploadedFiles)

// Paper properties
const paperTitle = ref('Breast Cancer Segmentation Using Deep Learning')
const paperAuthors = ref('Smith, J., et al.')
const paperYear = ref('2023')
const paperAbstract = ref('This study presents a novel approach to automated breast cancer segmentation using deep learning techniques on DCE-MRI scans.')

// Investigation properties
const investigationTitle = ref('Automated Tumor Detection Investigation')
const investigationDescription = ref('Investigation of automated deep learning methods for breast tumor detection and segmentation in DCE-MRI images')
const investigationSubmissionDate = ref('2023-01-15')

// Study properties
const studyTitle = ref('MRI-based Segmentation Study')
const studyDescription = ref('Comprehensive study of U-Net based segmentation on breast MRI scans')
const studyNumSubjects = ref('384')
const studyDesign = ref('Retrospective cohort study')

// Assay properties
const assayName = ref('U-Net Training Assay')
const workflowSteps = ref<WorkflowStep[]>([
  { id: 'step-1', description: 'Data acquisition: Collect 120 MRI scans' },
  { id: 'step-2', description: 'Preprocessing: DICOM to NIfTI conversion' },
  { id: 'step-3', description: 'Normalization: Z-score normalization' },
  { id: 'step-4', description: 'Training: U-Net model with Adam optimizer' },
  { id: 'step-5', description: 'Validation: 5-fold cross-validation' },
  { id: 'step-6', description: 'Evaluation: Calculate DICE scores' },
])

// Expand when files are uploaded
watch(() => props.hasUploadedFiles, (hasFiles) => {
  if (hasFiles) {
    isExpanded.value = true
  }
})

function handleNodeClick(id: string, type: SelectedItem['type'], name: string, event?: Event) {
  if (event) {
    event.stopPropagation()
  }
  
  // Toggle selection
  if (selectedItem.value?.id === id) {
    selectedItem.value = null
    if (type === 'assay') {
      emit('selectAssay', null)
    }
  } else {
    selectedItem.value = { id, type, name }
    if (type === 'assay') {
      emit('selectAssay', id)
    } else {
      emit('selectAssay', null)
    }
  }
}

function addStep() {
  workflowSteps.value.push({
    id: `step-${Date.now()}`,
    description: 'New workflow step'
  })
}

function removeStep(stepId: string) {
  workflowSteps.value = workflowSteps.value.filter(s => s.id !== stepId)
}

function _updateStep(stepId: string, description: string) {
  const step = workflowSteps.value.find(s => s.id === stepId)
  if (step) {
    step.description = description
  }
}
void _updateStep

const selectedItemClass = 'bg-blue-50 border border-blue-200'
const hoverClass = 'hover:bg-slate-50'
</script>

<template>
  <!-- Collapsed state -->
  <div v-if="!isExpanded" class="border-b border-slate-200 bg-white">
    <button
      @click="isExpanded = true"
      class="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50 transition-colors"
    >
      <div class="flex items-center gap-2 flex-1">
        <button
          @click.stop="emit('collapseLeftPanel')"
          class="text-slate-400 hover:text-slate-600 transition-colors"
        >
          <ChevronLeft class="w-4 h-4" />
        </button>
        <div class="text-left">
          <span class="text-sm font-medium text-slate-700">2. Review Study Design</span>
          <p class="text-xs text-slate-500">ISA (Investigation, Study, Assay) Hierarchy</p>
        </div>
      </div>
      <ChevronRight class="w-4 h-4 text-slate-400" />
    </button>
  </div>

  <!-- Expanded state -->
  <div v-else class="flex-1 border-b border-slate-200 bg-white flex flex-col overflow-hidden">
    <!-- Header -->
    <button
      @click="isExpanded = !isExpanded"
      :class="[
        'w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50 transition-colors',
        isExpanded ? 'border-b border-slate-200' : ''
      ]"
    >
      <div class="flex items-center gap-2 flex-1">
        <button
          @click.stop="emit('collapseLeftPanel')"
          class="text-slate-400 hover:text-slate-600 transition-colors"
        >
          <ChevronLeft class="w-4 h-4" />
        </button>
        <div class="text-left">
          <span class="text-sm font-medium text-slate-700">2. Review Study Design</span>
          <p class="text-xs text-slate-500">ISA (Investigation, Study, Assay) Hierarchy</p>
        </div>
      </div>
      <ChevronDown v-if="isExpanded" class="w-4 h-4 text-slate-400" />
      <ChevronRight v-else class="w-4 h-4 text-slate-400" />
    </button>

    <!-- Tree View -->
    <template v-if="hasUploadedFiles">
      <ResizablePanel
        orientation="vertical"
        :default-height="300"
        :min-height="150"
        :max-height="600"
      >
        <div class="px-3 py-3 space-y-1 overflow-auto h-full">
        <div class="space-y-1">
          <!-- Paper -->
          <div
            :class="[
              'flex items-center gap-2 p-2 rounded cursor-pointer transition-colors',
              selectedItem?.id === 'root' ? selectedItemClass : hoverClass
            ]"
            @click="handleNodeClick('root', 'paper', 'Breast Cancer Segmentation Using Deep Learning', $event)"
          >
            <FileText class="w-4 h-4 text-blue-600" />
            <span class="text-sm font-medium text-slate-900 truncate">
              Breast Cancer Segmentation Using Dee...
            </span>
          </div>

          <div class="ml-6 space-y-1">
            <!-- Investigation -->
            <div
              :class="[
                'flex items-center gap-2 p-2 rounded cursor-pointer transition-colors',
                selectedItem?.id === 'inv-1' ? selectedItemClass : hoverClass
              ]"
              @click="handleNodeClick('inv-1', 'investigation', 'Automated Tumor Detection Investigation', $event)"
            >
              <BookOpen class="w-4 h-4 text-green-600" />
              <span class="text-sm text-slate-700 truncate">Automated Tumor Detection Investig...</span>
            </div>

            <div class="ml-6 space-y-1">
              <!-- Study -->
              <div
                :class="[
                  'flex items-center gap-2 p-2 rounded cursor-pointer transition-colors',
                  selectedItem?.id === 'study-1' ? selectedItemClass : hoverClass
                ]"
                @click="handleNodeClick('study-1', 'study', 'MRI-based Segmentation Study', $event)"
              >
                <Layers class="w-4 h-4 text-purple-600" />
                <span class="text-sm text-slate-700">MRI-based Segmentation Study</span>
              </div>

              <div class="ml-6 space-y-1">
                <!-- Assay 1 -->
                <div
                  :class="[
                    'flex items-center gap-2 p-2 rounded cursor-pointer transition-colors',
                    selectedItem?.id === 'assay-1' ? selectedItemClass : hoverClass
                  ]"
                  @click="handleNodeClick('assay-1', 'assay', 'U-Net Training Assay', $event)"
                >
                  <FlaskConical class="w-4 h-4 text-orange-600" />
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                      <p class="text-sm text-slate-700">U-Net Training Assay</p>
                      <span class="text-xs text-slate-500">(6 steps)</span>
                    </div>
                  </div>
                </div>

                <!-- Assay 2 -->
                <div
                  :class="[
                    'flex items-center gap-2 p-2 rounded cursor-pointer transition-colors',
                    selectedItem?.id === 'assay-2' ? selectedItemClass : hoverClass
                  ]"
                  @click="handleNodeClick('assay-2', 'assay', 'Model Inference Assay', $event)"
                >
                  <FlaskConical class="w-4 h-4 text-orange-600" />
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                      <p class="text-sm text-slate-700">Model Inference Assay</p>
                      <span class="text-xs text-slate-500">(4 steps)</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        </div>
      </ResizablePanel>

      <!-- Property Editor -->
      <div class="flex-1 overflow-auto border-slate-200">
        <!-- No selection -->
        <div v-if="!selectedItem" class="p-4 text-center text-slate-400">
          <p class="text-sm">Select an item to edit properties</p>
        </div>

        <!-- Paper Properties -->
        <div v-else-if="selectedItem.type === 'paper'" class="p-4 space-y-4">
          <div class="border-b border-slate-200 pb-3 flex items-center justify-between">
            <div>
              <h3 class="font-medium text-slate-900">Paper Properties</h3>
              <p class="text-xs text-slate-500 mt-0.5">{{ selectedItem.name }}</p>
            </div>
            <button @click="selectedItem = null" class="text-slate-400 hover:text-slate-600 transition-colors">
              <X class="w-4 h-4" />
            </button>
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-medium text-slate-700">Title</label>
              <button @click="emit('sourceClick', 'paper-title')" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                <ExternalLink class="w-3 h-3" /> Source
              </button>
            </div>
            <input type="text" v-model="paperTitle" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-medium text-slate-700">Authors</label>
              <button @click="emit('sourceClick', 'paper-authors')" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                <ExternalLink class="w-3 h-3" /> Source
              </button>
            </div>
            <input type="text" v-model="paperAuthors" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-medium text-slate-700">Publication Year</label>
              <button @click="emit('sourceClick', 'paper-year')" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                <ExternalLink class="w-3 h-3" /> Source
              </button>
            </div>
            <input type="text" v-model="paperYear" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-medium text-slate-700">Abstract</label>
              <button @click="emit('sourceClick', 'paper-abstract')" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                <ExternalLink class="w-3 h-3" /> Source
              </button>
            </div>
            <textarea v-model="paperAbstract" rows="4" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
          </div>

          <button class="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors">
            Save Changes
          </button>
        </div>

        <!-- Investigation Properties -->
        <div v-else-if="selectedItem.type === 'investigation'" class="p-4 space-y-4">
          <div class="border-b border-slate-200 pb-3 flex items-center justify-between">
            <div>
              <h3 class="font-medium text-slate-900">Investigation Properties</h3>
              <p class="text-xs text-slate-500 mt-0.5">{{ selectedItem.name }}</p>
            </div>
            <button @click="selectedItem = null" class="text-slate-400 hover:text-slate-600 transition-colors">
              <X class="w-4 h-4" />
            </button>
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-medium text-slate-700">Title</label>
              <button @click="emit('sourceClick', 'inv-title')" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                <ExternalLink class="w-3 h-3" /> Source
              </button>
            </div>
            <input type="text" v-model="investigationTitle" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-medium text-slate-700">Description</label>
              <button @click="emit('sourceClick', 'inv-description')" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                <ExternalLink class="w-3 h-3" /> Source
              </button>
            </div>
            <textarea v-model="investigationDescription" rows="3" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-medium text-slate-700">Submission Date</label>
              <button @click="emit('sourceClick', 'inv-date')" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                <ExternalLink class="w-3 h-3" /> Source
              </button>
            </div>
            <input type="date" v-model="investigationSubmissionDate" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>

          <button class="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors">
            Save Changes
          </button>
        </div>

        <!-- Study Properties -->
        <div v-else-if="selectedItem.type === 'study'" class="p-4 space-y-4">
          <div class="border-b border-slate-200 pb-3 flex items-center justify-between">
            <div>
              <h3 class="font-medium text-slate-900">Study Properties</h3>
              <p class="text-xs text-slate-500 mt-0.5">{{ selectedItem.name }}</p>
            </div>
            <button @click="selectedItem = null" class="text-slate-400 hover:text-slate-600 transition-colors">
              <X class="w-4 h-4" />
            </button>
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-medium text-slate-700">Study Title</label>
              <button @click="emit('sourceClick', 'study-title')" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                <ExternalLink class="w-3 h-3" /> Source
              </button>
            </div>
            <input type="text" v-model="studyTitle" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-medium text-slate-700">Description</label>
              <button @click="emit('sourceClick', 'study-description')" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                <ExternalLink class="w-3 h-3" /> Source
              </button>
            </div>
            <textarea v-model="studyDescription" rows="3" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-medium text-slate-700">Number of Subjects</label>
              <button @click="emit('sourceClick', 'study-subjects')" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                <ExternalLink class="w-3 h-3" /> Source
              </button>
            </div>
            <input type="number" v-model="studyNumSubjects" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-medium text-slate-700">Study Design</label>
              <button @click="emit('sourceClick', 'study-design')" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                <ExternalLink class="w-3 h-3" /> Source
              </button>
            </div>
            <select v-model="studyDesign" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option>Retrospective cohort study</option>
              <option>Prospective cohort study</option>
              <option>Case-control study</option>
              <option>Cross-sectional study</option>
              <option>Randomized controlled trial</option>
            </select>
          </div>

          <button class="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors">
            Save Changes
          </button>
        </div>

        <!-- Assay Properties -->
        <div v-else-if="selectedItem.type === 'assay'" class="p-4 space-y-4">
          <div class="border-b border-slate-200 pb-3 flex items-center justify-between">
            <div>
              <h3 class="font-medium text-slate-900">Assay Properties</h3>
              <p class="text-xs text-slate-500 mt-0.5">{{ selectedItem.name }}</p>
            </div>
            <button
              @click="selectedItem = null"
              class="text-slate-400 hover:text-slate-600 transition-colors"
            >
              <X class="w-4 h-4" />
            </button>
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-medium text-slate-700">Name</label>
              <button
                @click="emit('sourceClick', 'assay-name')"
                class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1"
              >
                <ExternalLink class="w-3 h-3" />
                Source
              </button>
            </div>
            <input
              type="text"
              v-model="assayName"
              class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-slate-700">Workflow Steps</label>
              <button
                @click="addStep"
                class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1"
              >
                <Plus class="w-3 h-3" />
                Add Step
              </button>
            </div>
            
            <div class="space-y-2">
              <div v-for="(step, index) in workflowSteps" :key="step.id" class="relative">
                <div class="flex items-start gap-2">
                  <span class="text-xs text-slate-500 mt-2 w-6">{{ index + 1 }}.</span>
                  <input
                    type="text"
                    v-model="step.description"
                    class="flex-1 px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    @click="emit('sourceClick', `step-${step.id}`)"
                    class="text-blue-600 hover:text-blue-700 p-2"
                  >
                    <ExternalLink class="w-3 h-3" />
                  </button>
                  <button
                    @click="removeStep(step.id)"
                    class="text-red-400 hover:text-red-600 p-2"
                  >
                    <X class="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          <button class="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors">
            Save Changes
          </button>
        </div>
      </div>

      <!-- Assemble Button -->
      <div v-if="selectedAssay && hasUploadedFiles" class="border-t border-slate-200 p-3 flex-shrink-0">
        <button
          class="w-full px-4 py-2 text-sm rounded transition-colors bg-blue-600 text-white hover:bg-blue-700"
          @click="emit('assembleClick')"
        >
          Assemble Selected Assay
        </button>
      </div>
    </template>

    <!-- Empty state when no files uploaded -->
    <div v-else class="flex-1 flex items-center justify-center text-slate-400 bg-slate-50">
      <div class="text-center px-4">
        <svg class="w-10 h-10 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p class="text-xs">Upload a publication to begin</p>
      </div>
    </div>
  </div>
</template>
