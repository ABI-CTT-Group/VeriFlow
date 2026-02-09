<script setup lang="ts">
import { ref } from 'vue'
import { 
  Folder as FolderIcon, 
  FolderOpen as FolderOpenIcon, 
  File as FileIcon, 
  ChevronRight as ChevronRightIcon, 
  ChevronDown as ChevronDownIcon 
} from 'lucide-vue-next'

interface FileNode {
  name: string
  type: 'file' | 'folder'
  children?: FileNode[]
  extension?: string
}

interface Props {
  node: FileNode & { path?: string }
  depth?: number
  selectedPath?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  depth: 0,
  selectedPath: null
})

const emit = defineEmits<{
  fileClick: [node: FileNode]
}>()

const isExpanded = ref(props.depth < 2)

function toggleExpand() {
  isExpanded.value = !isExpanded.value
}

function handleClick() {
  if (props.node.type === 'file') {
    emit('fileClick', props.node)
  } else {
    toggleExpand()
  }
}
</script>

<template>
  <div>
    <div
      :data-tour="node.extension === 'nii.gz' || node.extension === 'nii' ? 'nii-file' : undefined"
      class="flex items-center gap-2 px-2 py-1 cursor-pointer rounded transition-colors"
      :class="{ 
        'bg-blue-100/50 hover:bg-blue-100': selectedPath && node.path === selectedPath,
        'hover:bg-slate-100': !selectedPath || node.path !== selectedPath
      }"
      :style="{ paddingLeft: depth * 20 + 12 + 'px' }"
      @click="handleClick"
    >
      <template v-if="node.type === 'folder'">
        <component :is="isExpanded ? ChevronDownIcon : ChevronRightIcon" class="w-4 h-4 text-slate-400" />
        <component :is="isExpanded ? FolderOpenIcon : FolderIcon" class="w-4 h-4 text-blue-500" />
        <span class="text-sm text-slate-700 font-medium">{{ node.name }}</span>
      </template>
      <template v-else>
        <FileIcon :class="['w-4 h-4', selectedPath && node.path === selectedPath ? 'text-blue-500' : 'text-slate-400']" />
        <span :class="['text-sm', selectedPath && node.path === selectedPath ? 'text-blue-700 font-medium' : 'text-slate-700']">{{ node.name }}</span>
      </template>
    </div>
    <div v-if="node.type === 'folder' && isExpanded && node.children">
      <FileTreeNode
        v-for="(child, index) in node.children"
        :key="index"
        :node="child"
        :depth="depth + 1"
        :selected-path="selectedPath"
        @file-click="$emit('fileClick', $event)"
      />
    </div>
  </div>
</template>
