<script setup lang="ts">
/**
 * DatasetNavigationModule.vue
 * Ported from: planning/UI/src/components/DatasetNavigationModule.tsx
 * 
 * File tree viewer for SDS-structured datasets with file preview.
 */
import { ref, computed } from 'vue'
import { Eye, Download, Edit, Image } from 'lucide-vue-next'
import ResizablePanel from '../layout/ResizablePanel.vue'
import FileTreeNode from './FileTreeNode.vue'

interface Props {
  selectedNode?: any
  defaultViewerPlugin?: string
  selectedDatasetId?: string | null
}

interface FileNode {
  name: string
  type: 'file' | 'folder'
  children?: FileNode[]
  extension?: string
}

const props = withDefaults(defineProps<Props>(), {
  selectedNode: null,
  defaultViewerPlugin: 'auto',
  selectedDatasetId: null,
})

const selectedFile = ref<string | null>(null)

// Map dataset IDs to their display names
const datasetNameMap: Record<string, string> = {
  'dce-mri-scans': 'DCE-MRI-Scans',
  'tumor-segmentation': 'Tumor-Segmentation'
}

// Generate file tree based on selected node or dataset
function generateFileTree(): FileNode[] {
  // If a specific dataset is selected, use its name
  if (props.selectedDatasetId && datasetNameMap[props.selectedDatasetId]) {
    const datasetName = datasetNameMap[props.selectedDatasetId]
    
    return [{
      name: datasetName,
      type: 'folder',
      children: [
        { name: 'dataset_description.json', type: 'file', extension: 'json' },
        { name: 'subjects.tsv', type: 'file', extension: 'tsv' },
        {
          name: 'primary',
          type: 'folder',
          children: [
            {
              name: 'Subject_001',
              type: 'folder',
              children: [
                { name: 'T1w.nii.gz', type: 'file', extension: 'nii.gz' },
                { name: 'metadata.json', type: 'file', extension: 'json' }
              ]
            },
            {
              name: 'Subject_002',
              type: 'folder',
              children: [
                { name: 'T1w.nii.gz', type: 'file', extension: 'nii.gz' },
                { name: 'metadata.json', type: 'file', extension: 'json' }
              ]
            }
          ]
        },
        { name: 'code', type: 'folder', children: [] }
      ]
    }]
  }
  
  if (!props.selectedNode) {
    return [{
      name: 'No-Data-Object-Selected',
      type: 'folder',
      children: []
    }]
  }

  const nodeName = props.selectedNode.name?.replace(/\s+/g, '-') || 'Data-Object'
  
  // Generate different SDS structures based on node type
  if (props.selectedNode.type === 'measurement' && props.selectedNode.role === 'input') {
    return [{
      name: nodeName,
      type: 'folder',
      children: [
        { name: 'dataset_description.json', type: 'file', extension: 'json' },
        { name: 'subjects.tsv', type: 'file', extension: 'tsv' },
        {
          name: 'primary',
          type: 'folder',
          children: [
            {
              name: 'Subject_001',
              type: 'folder',
              children: [
                { name: 'T1w.nii.gz', type: 'file', extension: 'nii.gz' },
                { name: 'metadata.json', type: 'file', extension: 'json' }
              ]
            }
          ]
        }
      ]
    }]
  } else if (props.selectedNode.type === 'tool') {
    return [{
      name: nodeName,
      type: 'folder',
      children: [
        { name: 'dataset_description.json', type: 'file', extension: 'json' },
        {
          name: 'code',
          type: 'folder',
          children: [
            { name: 'workflow.cwl', type: 'file', extension: 'cwl' },
            { name: 'Dockerfile', type: 'file', extension: 'docker' }
          ]
        }
      ]
    }]
  } else if (props.selectedNode.type === 'model') {
    return [{
      name: nodeName,
      type: 'folder',
      children: [
        { name: 'dataset_description.json', type: 'file', extension: 'json' },
        { name: 'model_description.json', type: 'file', extension: 'json' },
        {
          name: 'primary',
          type: 'folder',
          children: [
            { name: 'weights.pth', type: 'file', extension: 'pth' },
            { name: 'architecture.json', type: 'file', extension: 'json' }
          ]
        }
      ]
    }]
  }

  // Default structure
  return [{
    name: nodeName,
    type: 'folder',
    children: [
      { name: 'dataset_description.json', type: 'file', extension: 'json' },
      { name: 'README.md', type: 'file', extension: 'md' }
    ]
  }]
}

const fileTree = computed(() => generateFileTree())

function determineViewer(fileExtension?: string): string | null {
  if (props.defaultViewerPlugin !== 'auto') {
    return props.defaultViewerPlugin!
  }
  
  if (fileExtension === 'nii.gz' || fileExtension === 'nii') {
    return 'volview'
  } else if (['json', 'cwl', 'txt', 'md', 'yaml', 'docker'].includes(fileExtension || '')) {
    return 'editor'
  } else if (['png', 'jpg', 'jpeg'].includes(fileExtension || '')) {
    return 'image'
  }
  return null
}

const plugins = [
  { id: 'volview', name: 'VolView', icon: Eye, description: '3D Medical Image Viewer' },
  { id: 'editor', name: 'Code Editor', icon: Edit, description: 'Syntax-highlighted editor' },
  { id: 'image', name: 'Image Viewer', icon: Image, description: 'Image preview' }
]

const activePlugin = computed(() => {
  if (!selectedFile.value) return null
  
  // Find node in tree to get extension (simplified lookup)
  // In a real app we'd need better tree traversal
  const findExtension = (nodes: FileNode[]): string | undefined => {
    for (const node of nodes) {
      if (node.name === selectedFile.value) return node.extension
      if (node.children) {
        const found = findExtension(node.children)
        if (found) return found
      }
    }
    return undefined
  }
  
  const ext = findExtension(fileTree.value)
  return determineViewer(ext)
})

function handleFileClick(node: FileNode) {
  selectedFile.value = node.name
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-hidden">
    <!-- Dataset Navigation Panel -->
    <ResizablePanel 
      orientation="vertical" 
      title="Dataset Navigation" 
      :default-height="400"
      :min-height="150"
    >
      <div class="p-2">
        <FileTreeNode
          v-for="(node, index) in fileTree"
          :key="index"
          :node="node"
          @file-click="handleFileClick"
        />
      </div>
    </ResizablePanel>

    <!-- File View Panel -->
    <ResizablePanel 
      orientation="vertical" 
      title="File View" 
      :default-height="300"
      :min-height="150"
    >
      <div class="p-4">
        <div v-if="activePlugin" class="border border-slate-200 rounded-lg p-4 bg-slate-50">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
              <Eye v-if="activePlugin === 'volview'" class="w-5 h-5 text-blue-600" />
              <Edit v-else-if="activePlugin === 'editor'" class="w-5 h-5 text-blue-600" />
              <Image v-else-if="activePlugin === 'image'" class="w-5 h-5 text-blue-600" />
              <div>
                <span class="text-sm font-medium text-slate-900">
                  {{ plugins.find(p => p.id === activePlugin)?.name }}
                </span>
                <p v-if="selectedFile" class="text-xs text-slate-500">{{ selectedFile }}</p>
              </div>
            </div>
            <button @click="selectedFile = null" class="text-xs text-slate-500 hover:text-slate-700">
              Close
            </button>
          </div>
          <div class="bg-slate-900 rounded aspect-video flex items-center justify-center">
            <p class="text-slate-400 text-sm">
              <span v-if="activePlugin === 'volview'">3D Visualization Placeholder</span>
              <span v-else-if="activePlugin === 'editor'">Code Editor Placeholder</span>
              <span v-else-if="activePlugin === 'image'">Image Preview Placeholder</span>
            </p>
          </div>
        </div>
        <div v-else class="flex items-center justify-center h-full text-slate-400">
          <div class="text-center">
            <Eye class="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p class="text-sm">No file selected</p>
            <p class="text-xs mt-1">Click on a file in the tree above to view it</p>
          </div>
        </div>
      </div>
    </ResizablePanel>

    <!-- Export Section -->
    <div class="border-t border-slate-200 p-3 flex-shrink-0 bg-white">
      <div class="space-y-2">
        <button class="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors">
          <Download class="w-4 h-4" />
          Export Selected Data Object
        </button>
        <button class="w-full flex items-center justify-center gap-2 px-4 py-2 border border-slate-300 text-slate-700 text-sm rounded hover:bg-slate-50 transition-colors">
          <Download class="w-4 h-4" />
          Export All Data Objects
        </button>
        <p class="text-xs text-slate-400 text-center mt-2">
          Exports are packaged in SDS format
        </p>
      </div>
    </div>
  </div>
</template>
