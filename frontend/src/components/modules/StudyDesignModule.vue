<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { 
  FileText, BookOpen, Layers, FlaskConical, 
  ChevronLeft, ExternalLink, X, Plus, Loader2, Info
} from 'lucide-vue-next'
import { useWorkflowStore } from '../../stores/workflow'
import { storeToRefs } from 'pinia'

interface Props {
  selectedAssay: string | null
  hasUploadedFiles: boolean
}

// Store access
const workflowStore = useWorkflowStore()
const { hierarchy, isLoading, loadingMessage } = storeToRefs(workflowStore)

interface SelectedItem {
  id: string
  type: 'paper' | 'investigation' | 'study' | 'assay'
  name: string
  data?: any // Hold reference to the actual data object
}

interface WorkflowStep {
  id: string
  description: string
  tool: {
          id: string,
          name: string
        }
  input: Array<{ name: string, type: string }>
  output: Array<{ name: string, type: string }>
}

withDefaults(defineProps<Props>(), {
  selectedAssay: null,
  hasUploadedFiles: false,
})

const emit = defineEmits<{
  selectAssay: [assayId: string | null]
  sourceClick: [propertyId: string]
  assembleClick: []
  collapseLeftPanel: []
  propertiesOpened: []
}>()

const selectedItem = ref<SelectedItem | null>(null)

// --- Computed Properties for Reactivity ---

// Helper to safely access hierarchy parts
const investigation = computed(() => hierarchy.value)
const study = computed(() => investigation.value?.studies?.[0])
const assays = computed(() => study.value?.assays || [])

// Values used in template, now reactive
// Note: In a real edit scenario, we'd need local state initialized from these computed values
// For now, we display the store values directly or fallback

const paperTitle = computed({
  get: () => hierarchy.value?.paper?.title || 'No Paper Title',
  set: (val) => { if (hierarchy.value?.paper) hierarchy.value.paper.title = val }
})
const paperAuthors = computed({
  get: () => hierarchy.value?.paper?.authors || 'Unknown Authors',
  set: (val) => { if (hierarchy.value?.paper) hierarchy.value.paper.authors = val }
})
const paperYear = computed({
  get: () => hierarchy.value?.paper?.year || '',
  set: (val) => { if (hierarchy.value?.paper) hierarchy.value.paper.year = val }
})
const paperAbstract = computed({
  get: () => hierarchy.value?.paper?.abstract || '',
  set: (val) => { if (hierarchy.value?.paper) hierarchy.value.paper.abstract = val }
})

const investigationTitle = computed({
  get: () => investigation.value?.title || 'No Investigation',
  set: (val) => { if (investigation.value) investigation.value.title = val }
})
const investigationDescription = computed({
    get: () => investigation.value?.description || '',
    set: (val) => { if (investigation.value) investigation.value.description = val }
})
const investigationSubmissionDate = ref('2024-06-20') // Not in current interface

const studyTitle = computed({
    get: () => study.value?.title || 'No Study',
    set: (val) => { if (study.value) study.value.title = val }
})
const studyDescription = computed({
    get: () => study.value?.description || '',
    set: (val) => { if (study.value) study.value.description = val }
})
const studyNumSubjects = ref('1506') // Not explicitly in Study interface
const studyDesign = ref('Retrospective multicenter cohort study')

// Assay Handling
// When an assay is selected, populate the local editable state
const assayName = ref('')
const workflowSteps = ref<WorkflowStep[]>([])

// Watch for selection changes to update local assay state
watch(() => selectedItem.value, (newItem) => {
    if (newItem?.type === 'assay' && newItem.data) {
        assayName.value = newItem.data.name || ''
        // Map store steps to UI steps
        workflowSteps.value = (newItem.data.steps || []).map((s: any) => ({
            id: s.id || `step-${Math.random()}`,
            description: s.description || s.name || 'Unknown Step'
        }))
    }
})

// --- Interaction Handlers ---

function handleNodeClick(id: string, type: SelectedItem['type'], name: string, data: any = null, event?: Event) {
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
    selectedItem.value = { id, type, name, data }
    emit('propertiesOpened')
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
    description: 'New workflow step',
    tool: {
      id: 'tool-1',
      name: 'Example Tool'
    },
    input: [],
    output: []
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

// --- New Feature Handler ---
const showNotImplemented = ref(false)

function handleSourceClick() {
  showNotImplemented.value = true
}
</script>

<template>
  <div class="flex-1 border-b border-slate-200 bg-white flex flex-col overflow-hidden h-full">
    <!-- Header -->
    <div
      class="w-full flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-white"
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
    </div>

    <!-- Content Area -->
    <template v-if="hasUploadedFiles">
      
      <!-- Loading State -->
      <div v-if="isLoading" class="flex-1 flex flex-col items-center justify-center p-8 space-y-4">
        <div class="relative w-16 h-16 flex items-center justify-center">
            <div class="absolute inset-0 border-4 border-slate-100 rounded-full"></div>
            <div class="absolute inset-0 border-4 border-blue-500 rounded-full border-t-transparent animate-spin"></div>
            <Loader2 class="w-6 h-6 text-blue-500 animate-bounce" />
        </div>
        <div class="text-center">
            <h3 class="text-slate-900 font-medium text-lg">Analyzing Publication</h3>
            <p class="text-slate-500 text-sm mt-1">{{ loadingMessage || 'Extracting study design and assay details...' }}</p>
        </div>
        <!-- Simple Progress Bar -->
        <div class="w-64 h-1.5 bg-slate-100 rounded-full overflow-hidden mt-2">
            <div class="h-full bg-blue-500 animate-pulse rounded-full w-2/3"></div>
        </div>
      </div>

      <div v-else class="flex-1 flex flex-col min-h-0 overflow-hidden">
        <!-- Tree View -->
        <div class="overflow-y-auto border-b border-slate-200 max-h-[50%] shrink-0">
          <div class="px-3 py-3 space-y-1">
              <!-- Paper -->
              <div
                :class="[
                  'flex items-center gap-2 p-2 rounded cursor-pointer transition-colors',
                  selectedItem?.id === 'root' ? selectedItemClass : hoverClass
                ]"
                @click="handleNodeClick('root', 'paper', paperTitle, null, $event)"
              >
                <FileText class="w-4 h-4 text-blue-600 flex-shrink-0" />
                <span class="text-sm font-medium text-slate-900 truncate">
                  {{ paperTitle }}
                </span>
              </div>

              <div class="ml-6 space-y-1">
                <!-- Investigation -->
                <div
                  :class="[
                    'flex items-center gap-2 p-2 rounded cursor-pointer transition-colors',
                    selectedItem?.id === investigation?.identifier ? selectedItemClass : hoverClass
                  ]"
                  @click="handleNodeClick(investigation?.identifier || 'inv-1', 'investigation', investigationTitle, investigation, $event)"
                >
                  <BookOpen class="w-4 h-4 text-green-600 flex-shrink-0" />
                  <span class="text-sm text-slate-700 truncate">{{ investigationTitle }}</span>
                </div>

                <div class="ml-6 space-y-1">
                  <!-- Study -->
                  <div
                    :class="[
                      'flex items-center gap-2 p-2 rounded cursor-pointer transition-colors',
                      selectedItem?.id === study?.identifier ? selectedItemClass : hoverClass
                    ]"
                    @click="handleNodeClick(study?.identifier || 'study-1', 'study', studyTitle, study, $event)"
                  >
                    <Layers class="w-4 h-4 text-purple-600 flex-shrink-0" />
                    <span class="text-sm text-slate-700 truncate">{{ studyTitle }}</span>
                  </div>

                  <div class="ml-6 space-y-1">
                    <!-- Dynamic Assays List -->
                    <div
                      v-for="assay in assays"
                      :key="assay.identifier"
                      :class="[
                        'flex items-center gap-2 p-2 rounded cursor-pointer transition-colors',
                        selectedItem?.id === assay.identifier ? selectedItemClass : hoverClass
                      ]"
                      @click="handleNodeClick(assay.identifier || 'u-assay', 'assay', assay.filename, assay, $event)"
                    >
                      <FlaskConical class="w-4 h-4 text-orange-600 flex-shrink-0" />
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2">
                          <p class="text-sm text-slate-700 truncate">{{ assay.filename }}</p>
                          <span class="text-xs text-slate-500 flex-shrink-0">({{ (assay.steps?.length || 0) }} steps)</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
          </div>
        </div>

        <!-- Property Editor -->
        <div class="flex-1 overflow-y-auto min-h-0 bg-slate-50/30">
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
                <button @click="handleSourceClick()" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                  <ExternalLink class="w-3 h-3" /> Source
                </button>
              </div>
              <input type="text" v-model="paperTitle" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>

            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-slate-700">Authors</label>
                <button @click="handleSourceClick()" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                  <ExternalLink class="w-3 h-3" /> Source
                </button>
              </div>
              <input type="text" v-model="paperAuthors" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>

            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-slate-700">Publication Year</label>
                <button @click="handleSourceClick()" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                  <ExternalLink class="w-3 h-3" /> Source
                </button>
              </div>
              <input type="text" v-model="paperYear" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>

            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-slate-700">Abstract</label>
                <button @click="handleSourceClick()" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
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
                <button @click="handleSourceClick()" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                  <ExternalLink class="w-3 h-3" /> Source
                </button>
              </div>
              <input type="text" v-model="investigationTitle" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>

            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-slate-700">Description</label>
                <button @click="handleSourceClick()" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                  <ExternalLink class="w-3 h-3" /> Source
                </button>
              </div>
              <textarea v-model="investigationDescription" rows="3" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
            </div>

            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-slate-700">Submission Date</label>
                <button @click="handleSourceClick()" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
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
                <button @click="handleSourceClick()" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                  <ExternalLink class="w-3 h-3" /> Source
                </button>
              </div>
              <input type="text" v-model="studyTitle" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>

            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-slate-700">Description</label>
                <button @click="handleSourceClick()" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                  <ExternalLink class="w-3 h-3" /> Source
                </button>
              </div>
              <textarea v-model="studyDescription" rows="3" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
            </div>

            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-slate-700">Number of Subjects</label>
                <button @click="handleSourceClick()" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                  <ExternalLink class="w-3 h-3" /> Source
                </button>
              </div>
              <input type="number" v-model="studyNumSubjects" class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>

            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-xs font-medium text-slate-700">Study Design</label>
                <button @click="handleSourceClick()" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
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
                  @click="handleSourceClick()"
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
                      v-model="step.tool.name"
                      class="flex-1 px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      @click="handleSourceClick()"
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
      </div>

      <!-- Assemble Button -->
      <div v-if="selectedAssay && hasUploadedFiles" class="border-t border-slate-200 p-3 flex-shrink-0 bg-white">
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


  <!-- Friendly Popup Modal -->
  <Teleport to="body">
    <div
      v-if="showNotImplemented"
      class="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm"
      @click="showNotImplemented = false"
    >
      <div
        class="bg-white rounded-xl shadow-2xl p-6 w-96 relative animate-in fade-in zoom-in duration-200"
        @click.stop
      >
        <button
          @click="showNotImplemented = false"
          class="absolute top-4 right-4 text-slate-400 hover:text-slate-600 transition-colors"
        >
          <X class="w-5 h-5" />
        </button>
        
        <div class="text-center pt-2">
          <div class="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <Info class="w-6 h-6 text-blue-600" />
          </div>
          
          <h3 class="text-lg font-semibold text-slate-900 mb-2">Coming Soon</h3>
          <p class="text-slate-500 text-sm mb-6 leading-relaxed">
            To be implemented in the future. We are currently working on this feature!
          </p>
          
          <button
            @click="showNotImplemented = false"
            class="w-full px-4 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 active:bg-blue-800 transition-all shadow-sm hover:shadow"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
