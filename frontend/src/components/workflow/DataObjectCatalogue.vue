<script setup lang="ts">
/**
 * DataObjectCatalogue.vue
 * Ported from: planning/UI/src/components/DataObjectCatalogue.tsx
 * 
 * Sidebar panel listing available data objects linked to workflow nodes.
 * Updated to include "Active" vs "All" tabs per React reference.
 */
import { ref, computed, watch, onMounted } from 'vue'
import { 
  Database, Beaker, Box, ChevronRight, ChevronDown, 
  ExternalLink, Minimize2 
} from 'lucide-vue-next'

interface Props {
  activeWorkflow?: boolean
  selectedNodeId?: string
  selectedDatasetId?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  activeWorkflow: false,
  selectedNodeId: undefined,
  selectedDatasetId: null,
})

const emit = defineEmits<{
  sourceClick: [propertyId: string]
  datasetSelect: [datasetId: string | null]
  collapse: []
}>()

// State
const activeTab = ref<'active' | 'all'>('active')
const expandedCategories = ref<Set<string>>(new Set())
const expandedItem = ref<string | null>(null)

// Mock Data (matching React DataObjectCatalogue.tsx)
const activeInputMeasurements = [
  {
    id: 'meas-active-1',
    name: 'DCE-MRI Scans',
    description: '384 subjects, T1-weighted, DICOM format',
    icon: 'database',
    inUse: true,
    nodeId: 'input-1' // Added for linking
  }
]

const activeOutputMeasurements = [
  {
    id: 'meas-active-2',
    name: 'Tumor Segmentation Masks',
    description: 'Ground truth annotations, NIfTI format',
    icon: 'database',
    inUse: true,
    nodeId: 'output-1'
  }
]

const activeTools = [
  {
    id: 'tool-active-1',
    name: 'DICOM to NIfTI',
    description: 'Converts DICOM to NIfTI using dcm2niix',
    icon: 'tool',
    inUse: true,
    nodeId: 'tool-1'
  },
  {
    id: 'tool-active-2',
    name: 'nnU-Net Segmentation',
    description: 'U-Net based tumor segmentation',
    icon: 'tool',
    inUse: true,
    nodeId: 'tool-2'
  },
  {
    id: 'tool-active-3',
    name: 'Post-processing',
    description: 'Refines segmentation masks',
    icon: 'tool',
    inUse: true,
    nodeId: 'tool-3'
  }
]

const activeModels = [
  {
    id: 'model-active-1',
    name: 'nnU-Net Pretrained Weights',
    description: 'Pretrained on medical imaging datasets',
    icon: 'box',
    inUse: true,
    nodeId: 'model-1'
  }
]

// All items (Active + others)
const allInputMeasurements = [
  ...activeInputMeasurements,
  {
    id: 'meas-3',
    name: 'Clinical Metadata',
    description: 'Patient demographics, tumor characteristics',
    icon: 'database',
    inUse: false
  }
]

const allOutputMeasurements = [
  ...activeOutputMeasurements,
  {
    id: 'meas-2',
    name: 'CT Segmentation Results',
    description: 'Segmentation outputs from CT scans',
    icon: 'database',
    inUse: false
  }
]

const allTools = [
  ...activeTools,
  {
    id: 'tool-3',
    name: 'Image Preprocessor',
    description: 'Normalization, registration, bias correction',
    icon: 'tool',
    inUse: false
  },
  {
    id: 'tool-4',
    name: 'Quality Control',
    description: 'Automated QC checks for outputs',
    icon: 'tool',
    inUse: false
  }
]

const allModels = [
  ...activeModels,
  {
    id: 'model-2',
    name: 'ResNet Classifier',
    description: 'Tumor classification model',
    icon: 'box',
    inUse: false
  }
]

// Computed lists based on tab
const inputMeasurements = computed(() => activeTab.value === 'active' ? activeInputMeasurements : allInputMeasurements)
const outputMeasurements = computed(() => activeTab.value === 'active' ? activeOutputMeasurements : allOutputMeasurements)
const tools = computed(() => activeTab.value === 'active' ? activeTools : allTools)
const models = computed(() => activeTab.value === 'active' ? activeModels : allModels)

const categoryCounts = computed(() => {
  const activeCount = activeInputMeasurements.length + activeOutputMeasurements.length + activeTools.length + activeModels.length
  const allCount = allInputMeasurements.length + allOutputMeasurements.length + allTools.length + allModels.length
  return { active: activeCount, all: allCount }
})

// Mappings for auto-selection (matching React)
const nodeToDataObjectMap: Record<string, string> = {
  'input-1': 'meas-active-1',
  'output-1': 'meas-active-2',
  'tool-1': 'tool-active-1',
  'tool-2': 'tool-active-2',
  'tool-3': 'tool-active-3',
  'model-1': 'model-active-1'
}

const datasetToDataObjectMap: Record<string, string> = {
  'dce-mri-scans': 'meas-active-1',
  'tumor-segmentation': 'meas-active-2'
}

// Helpers
function toggleSection(sectionId: string) {
  if (expandedCategories.value.has(sectionId)) {
    expandedCategories.value.delete(sectionId)
  } else {
    expandedCategories.value.add(sectionId)
  }
}

function toggleItem(itemId: string) {
  expandedItem.value = expandedItem.value === itemId ? null : itemId
}

function handleCollapseAll() {
  expandedCategories.value.clear()
  expandedItem.value = null
  emit('collapse')
}

function onDragStart(event: DragEvent, item: any, type: string) {
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'copy'
    event.dataTransfer.setData('application/json', JSON.stringify({ item, type }))
  }
}

function onSourceClick(propertyId: string) {
  emit('sourceClick', propertyId)
}

// Watchers for auto-expansion
watch(() => props.selectedNodeId, (nodeId) => {
  if (!nodeId) return
  const dataObjectId = nodeToDataObjectMap[nodeId]
  if (dataObjectId) {
    openItem(dataObjectId)
  }
}, { immediate: true })

watch(() => props.selectedDatasetId, (datasetId) => {
  if (!datasetId) return
  const dataObjectId = datasetToDataObjectMap[datasetId]
  if (dataObjectId) {
    openItem(dataObjectId)
  }
}, { immediate: true })

function openItem(dataObjectId: string) {
  // Find which section this object belongs to in order to expand it
  const allLists = [
    { id: 'input-measurements', items: allInputMeasurements },
    { id: 'output-measurements', items: allOutputMeasurements },
    { id: 'tools', items: allTools },
    { id: 'models', items: allModels }
  ]

  for (const list of allLists) {
    if (list.items.find(i => i.id === dataObjectId)) {
      expandedCategories.value.add(list.id)
      expandedItem.value = dataObjectId
      break
    }
  }
}

// Initial state
onMounted(() => {
  // Default open if nothing selected
  if (!props.selectedNodeId && !props.selectedDatasetId) {
    expandedCategories.value.add('input-measurements')
  }
})

</script>

<template>
  <div class="h-full flex flex-col bg-white">
    <!-- Header with Tabs -->
    <div class="border-b border-slate-200">
      <div class="p-4 flex items-start justify-between">
        <div class="flex-1">
          <h3 class="text-sm font-medium text-slate-900">Data Object Catalogue</h3>
          <p class="text-xs text-slate-500 mt-0.5">Browse and edit data objects</p>
        </div>
        <div class="flex items-center gap-1">
          <button
            @click="handleCollapseAll"
            class="px-2 py-1 text-xs text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded transition-colors flex items-center gap-1"
            title="Collapse all sections"
          >
            <Minimize2 class="w-3 h-3" />
            Collapse All
          </button>
          <button
            @click="emit('collapse')"
            class="p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded transition-colors"
            title="Collapse panel"
          >
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>
      </div>
      
      <!-- Tabs -->
      <div class="flex border-t border-slate-200">
        <button
          @click="activeTab = 'active'"
          :class="[
            'flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'active'
              ? 'border-blue-600 text-blue-600 bg-blue-50'
              : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          ]"
        >
          Active ({{ categoryCounts.active }})
        </button>
        <button
          @click="activeTab = 'all'"
          :class="[
            'flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'all'
              ? 'border-blue-600 text-blue-600 bg-blue-50'
              : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          ]"
        >
          All ({{ categoryCounts.all }})
        </button>
      </div>
    </div>

    <!-- Data Object Lists -->
    <div class="flex-1 overflow-auto">
      
      <!-- Helper for SECTION -->
      <template v-for="section in [
        { title: 'Input Measurements', id: 'input-measurements', items: inputMeasurements, icon: Database, color: 'text-blue-600' },
        { title: 'Output Measurements', id: 'output-measurements', items: outputMeasurements, icon: Database, color: 'text-blue-600' },
        { title: 'Tools', id: 'tools', items: tools, icon: Beaker, color: 'text-purple-600' },
        { title: 'Models', id: 'models', items: models, icon: Box, color: 'text-green-600' }
      ]" :key="section.id">
        
        <div class="border-b border-slate-200">
          <button
            @click="toggleSection(section.id)"
            class="w-full flex items-center gap-2 px-4 py-3 hover:bg-slate-50 transition-colors"
          >
            <ChevronDown 
              v-if="expandedCategories.has(section.id)" 
              class="w-4 h-4 text-slate-400" 
            />
            <ChevronRight 
              v-else 
              class="w-4 h-4 text-slate-400"
            />
            <component :is="section.icon" :class="['w-4 h-4', section.color]" />
            <span class="text-sm font-medium text-slate-900">{{ section.title }}</span>
            <span class="text-xs text-slate-500">({{ section.items.length }})</span>
          </button>
          
          <div v-show="expandedCategories.has(section.id)" class="pb-2">
            <div v-for="item in section.items" :key="item.id">
              <div
                class="mx-3 mb-2 bg-white border border-slate-200 rounded-lg overflow-hidden hover:shadow-sm hover:border-blue-300 transition-all cursor-pointer"
                @click="toggleItem(item.id)"
                :draggable="true"
                @dragstart="(e) => onDragStart(e, item, section.title.includes('Measure') ? 'measurement' : section.id.slice(0, -1))"
              >
                <div class="flex items-start gap-2 p-3">
                  <Database v-if="section.id.includes('measure')" class="w-4 h-4 text-slate-300 mt-0.5" />
                  <component :is="section.icon" :class="['w-5 h-5 mt-0.5 flex-shrink-0', section.color]" />
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                      <p class="text-sm font-medium text-slate-900">{{ item.name }}</p>
                      <span v-if="item.inUse" class="px-1.5 py-0.5 text-xs bg-green-100 text-green-700 rounded">In Use</span>
                    </div>
                    <p class="text-xs text-slate-500 mt-0.5">{{ item.description }}</p>
                  </div>
                  <component :is="expandedItem === item.id ? ChevronDown : ChevronRight" class="w-4 h-4 text-slate-400 flex-shrink-0" />
                </div>
              </div>
              
              <!-- Property Editor (Expanded) -->
              <div v-if="expandedItem === item.id" class="mx-3 mb-2 bg-white border border-slate-200 rounded-lg overflow-hidden">
                <div class="px-3 py-2 bg-slate-100 border-b border-slate-200 flex items-center gap-2">
                  <div class="flex items-center gap-2 flex-1">
                     <component :is="section.icon" class="w-4 h-4 text-slate-400" />
                     <span class="text-xs font-medium text-slate-700">Editing: {{ item.name }}</span>
                  </div>
                </div>
                
                <div class="p-3 space-y-3 bg-white">
                  <div>
                    <div class="flex items-center justify-between mb-1">
                      <label class="text-xs font-medium text-slate-700">Name</label>
                      <button @click.stop="onSourceClick(`${item.id}-name`)" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                        <ExternalLink class="w-3 h-3" /> Source
                      </button>
                    </div>
                    <input type="text" :value="item.name" class="w-full px-2 py-1.5 text-xs border border-slate-300 rounded hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white" />
                  </div>
                  <div>
                    <div class="flex items-center justify-between mb-1">
                      <label class="text-xs font-medium text-slate-700">Description</label>
                      <button @click.stop="onSourceClick(`${item.id}-desc`)" class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                        <ExternalLink class="w-3 h-3" /> Source
                      </button>
                    </div>
                    <textarea :value="item.description" rows="3" class="w-full px-2 py-1.5 text-xs border border-slate-300 rounded hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white" />
                  </div>
                  <div>
                    <label class="text-xs font-medium text-slate-700 block mb-1">Type</label>
                    <select class="w-full px-2 py-1.5 text-xs border border-slate-300 rounded hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
                      <option>{{ item.icon }}</option>
                    </select>
                  </div>
                  <button class="w-full px-3 py-1.5 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors">
                    Save Changes
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

    </div>
  </div>
</template>
