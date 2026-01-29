<script setup lang="ts">
/**
 * ConfigurationPanel.vue
 * Ported from: planning/UI/src/components/ConfigurationPanel.tsx
 * 
 * Settings dropdown with general options and plugin management.
 */
import { ref } from 'vue'
import { Settings, X, Plus, Trash2 } from 'lucide-vue-next'

interface Props {
  defaultViewerPlugin?: string
}

interface Plugin {
  id: string
  name: string
  version: string
  enabled: boolean
}

const _props = withDefaults(defineProps<Props>(), {
  defaultViewerPlugin: 'auto',
})

void _props // Mark as intentionally used

const emit = defineEmits<{
  viewerPluginChange: [plugin: string]
}>()

const isOpen = ref(false)
const activeTab = ref<'general' | 'plugins'>('general')
const reanalysisMode = ref<'manual' | 'auto'>('manual')
const saveIntermediateResults = ref(false)

const plugins = ref<Plugin[]>([
  { id: '1', name: 'BIDS Validator', version: '1.2.0', enabled: true },
  { id: '2', name: 'SPARC Exporter', version: '2.0.1', enabled: true },
  { id: '3', name: 'CWL Generator', version: '1.5.0', enabled: false }
])

function togglePlugin(id: string) {
  const plugin = plugins.value.find(p => p.id === id)
  if (plugin) {
    plugin.enabled = !plugin.enabled
  }
}

function removePlugin(id: string) {
  plugins.value = plugins.value.filter(p => p.id !== id)
}
</script>

<template>
  <div class="relative">
    <button
      @click="isOpen = !isOpen"
      class="flex items-center gap-2 px-3 py-1.5 text-sm border border-slate-300 rounded hover:bg-slate-50"
    >
      <Settings class="w-4 h-4" />
      Configuration
    </button>

    <template v-if="isOpen">
      <!-- Backdrop -->
      <div class="fixed inset-0 z-40" @click="isOpen = false" />
      
      <!-- Panel -->
      <div class="absolute right-0 top-full mt-2 w-96 bg-white border border-slate-200 rounded-lg shadow-xl z-50">
        <div class="p-4 border-b border-slate-200 flex items-center justify-between">
          <h3 class="font-medium text-slate-900">Configuration</h3>
          <button @click="isOpen = false" class="text-slate-400 hover:text-slate-600">
            <X class="w-4 h-4" />
          </button>
        </div>

        <!-- Tabs -->
        <div class="flex border-b border-slate-200">
          <button
            @click="activeTab = 'general'"
            :class="[
              'flex-1 px-4 py-2 text-sm font-medium transition-colors',
              activeTab === 'general'
                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            ]"
          >
            General
          </button>
          <button
            @click="activeTab = 'plugins'"
            :class="[
              'flex-1 px-4 py-2 text-sm font-medium transition-colors',
              activeTab === 'plugins'
                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            ]"
          >
            Plugins
          </button>
        </div>

        <div class="p-4 space-y-4 max-h-96 overflow-y-auto">
          <!-- General Tab -->
          <template v-if="activeTab === 'general'">
            <!-- Re-analysis Mode -->
            <div>
              <label class="text-sm font-medium text-slate-700 block mb-2">
                Scholar Re-analysis Mode
              </label>
              <div class="space-y-2">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="reanalysis"
                    value="manual"
                    v-model="reanalysisMode"
                    class="text-blue-600"
                  />
                  <div>
                    <p class="text-sm text-slate-900">Manual</p>
                    <p class="text-xs text-slate-500">Re-analyze only when button is pressed</p>
                  </div>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="reanalysis"
                    value="auto"
                    v-model="reanalysisMode"
                    class="text-blue-600"
                  />
                  <div>
                    <p class="text-sm text-slate-900">Automatic</p>
                    <p class="text-xs text-slate-500">Re-analyze after each property edit</p>
                  </div>
                </label>
              </div>
            </div>

            <!-- Workflow Options -->
            <div class="pt-3 border-t border-slate-200">
              <label class="text-sm font-medium text-slate-700 block mb-2">
                Workflow Execution
              </label>
              <label class="flex items-start gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  v-model="saveIntermediateResults"
                  class="mt-1 text-blue-600"
                />
                <div>
                  <p class="text-sm text-slate-900">Save Intermediate Results</p>
                  <p class="text-xs text-slate-500">Serialize transient outputs as SDS datasets</p>
                </div>
              </label>
            </div>

            <!-- Default File Viewer -->
            <div class="pt-3 border-t border-slate-200">
              <label class="text-sm font-medium text-slate-700 block mb-2">
                Default File Viewer
              </label>
              <select
                :value="defaultViewerPlugin"
                @change="emit('viewerPluginChange', ($event.target as HTMLSelectElement).value)"
                class="w-full px-3 py-2 text-sm border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="auto">Auto-detect (based on file type)</option>
                <option value="volview">VolView (3D Medical Imaging)</option>
                <option value="editor">Code Editor</option>
                <option value="image">Image Viewer</option>
              </select>
              <p class="text-xs text-slate-500 mt-1">
                Plugin used when viewing files in Results panel
              </p>
            </div>

            <!-- Status -->
            <div class="pt-3 border-t border-slate-200">
              <div class="space-y-2 text-xs">
                <div class="flex justify-between">
                  <span class="text-slate-600">Active Agents</span>
                  <span class="text-slate-900 font-medium">3/3</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-slate-600">Airflow Status</span>
                  <span class="text-green-600 font-medium">Connected</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-slate-600">Current Phase</span>
                  <span class="text-slate-900 font-medium">Stage 3</span>
                </div>
              </div>
            </div>
          </template>

          <!-- Plugins Tab -->
          <template v-else>
            <div>
              <div class="flex items-center justify-between mb-3">
                <label class="text-sm font-medium text-slate-700">
                  Registered Plugins
                </label>
                <button class="text-blue-600 hover:text-blue-700 text-xs flex items-center gap-1">
                  <Plus class="w-3 h-3" />
                  Add Plugin
                </button>
              </div>
              
              <div class="space-y-2">
                <div
                  v-for="plugin in plugins"
                  :key="plugin.id"
                  class="flex items-center gap-3 p-3 bg-slate-50 border border-slate-200 rounded-lg"
                >
                  <input
                    type="checkbox"
                    :checked="plugin.enabled"
                    @change="togglePlugin(plugin.id)"
                    class="text-blue-600"
                  />
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-slate-900">{{ plugin.name }}</p>
                    <p class="text-xs text-slate-500">v{{ plugin.version }}</p>
                  </div>
                  <button
                    @click="removePlugin(plugin.id)"
                    class="text-red-400 hover:text-red-600 p-1"
                  >
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            <div class="pt-3 border-t border-slate-200">
              <p class="text-xs text-slate-500">
                Plugins extend VeriFlow functionality. View plugin outputs in the Viewer panel.
              </p>
            </div>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>
