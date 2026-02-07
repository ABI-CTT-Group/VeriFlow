<script setup lang="ts">
import { Upload, FileText, GitMerge, Play, X } from 'lucide-vue-next'

defineEmits<{
  (e: 'getStarted'): void
}>()
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center px-4">
    <!-- Backdrop with blur -->
    <div class="absolute inset-0 bg-slate-900/20 backdrop-blur-sm"></div>

    <!-- Main Card -->
    <div class="relative bg-white rounded-xl shadow-2xl max-w-4xl w-full text-slate-900 border border-slate-200 overflow-hidden">
        
      <!-- Close button -->
      <button 
        @click="$emit('getStarted')"
        class="absolute top-4 right-4 text-slate-400 hover:text-slate-600 transition-colors"
      >
        <X class="w-6 h-6" />
      </button>

      <div class="p-8 md:p-10">
        <!-- Header -->
        <div class="mb-8">
          <h1 class="text-3xl font-bold text-slate-900 mb-2">Welcome to <span class="text-blue-600">VeriFlow</span></h1>
          <p class="text-slate-500 text-lg">Your Autonomous Research Reproducibility Engineer</p>
        </div>

        <!-- Description -->
        <p class="text-slate-600 text-base mb-8 leading-relaxed max-w-3xl">
          VeriFlow solves the scientific reproducibility crisis by using AI agents to extract methodological logic from publications and create verifiable, executable research workflows.
        </p>

        <!-- Grid of steps -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <!-- Step 1 -->
          <div class="bg-slate-50 p-4 rounded-lg border border-slate-200 flex items-start gap-4">
            <div class="bg-blue-100 p-2 rounded-lg shrink-0">
              <Upload class="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h3 class="font-semibold text-slate-900 mb-1">1. Upload Publication</h3>
              <p class="text-sm text-slate-500">Drag and drop a research paper (PDF) to begin analysis</p>
            </div>
          </div>

          <!-- Step 2 -->
          <div class="bg-slate-50 p-4 rounded-lg border border-slate-200 flex items-start gap-4">
            <div class="bg-green-100 p-2 rounded-lg shrink-0">
              <FileText class="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h3 class="font-semibold text-slate-900 mb-1">2. Review Study Design</h3>
              <p class="text-sm text-slate-500">Scholar agent extracts methodology and parameters</p>
            </div>
          </div>

          <!-- Step 3 -->
          <div class="bg-slate-50 p-4 rounded-lg border border-slate-200 flex items-start gap-4">
            <div class="bg-purple-100 p-2 rounded-lg shrink-0">
              <GitMerge class="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h3 class="font-semibold text-slate-900 mb-1">3. Assemble and Execute Workflow</h3>
              <p class="text-sm text-slate-500">Engineering helps you assemble, run, and verify the workflow</p>
            </div>
          </div>

          <!-- Step 4 -->
          <div class="bg-slate-50 p-4 rounded-lg border border-slate-200 flex items-start gap-4">
            <div class="bg-red-100 p-2 rounded-lg shrink-0">
              <Play class="w-6 h-6 text-red-600" />
            </div>
            <div>
              <h3 class="font-semibold text-slate-900 mb-1">4. Visualise & Export</h3>
              <p class="text-sm text-slate-500">Reviewer agent highlights where descriptions came from in the paper with confidence scores</p>
            </div>
          </div>
        </div>

        <!-- Example Use Case Box -->
        <div class="bg-blue-50 border border-blue-100 rounded-lg p-5 mb-8">
          <h3 class="text-blue-700 font-semibold mb-2">Example Use Case</h3>
          <p class="text-slate-600 text-sm">
            This instance provides a demo showing how to segment breast tumours from medical images. Click Get Started to see VeriFlow in action!
          </p>
        </div>

        <!-- Footer Action -->
        <div class="flex justify-end">
          <button 
            @click="$emit('getStarted')"
            class="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 px-6 rounded-lg transition-colors cursor-pointer shadow-sm"
          >
            Get Started
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
