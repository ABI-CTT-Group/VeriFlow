<script setup lang="ts">
import Sidebar from './components/Sidebar.vue'
import MainContent from './components/MainContent.vue'
</script>

<template>
  <div class="app-container">
    <Sidebar />
    <MainContent />
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--color-bg-primary) 0%, var(--color-bg-secondary) 100%);
}
</style>
