<script setup lang="ts">
import { ref } from 'vue'
import { Upload, FileText, GitBranch, Terminal, Settings } from 'lucide-vue-next'

const activeTab = ref('upload')

const menuItems = [
  { id: 'upload', icon: Upload, label: 'Upload' },
  { id: 'study', icon: FileText, label: 'Study Design' },
  { id: 'workflow', icon: GitBranch, label: 'Workflow' },
  { id: 'console', icon: Terminal, label: 'Console' },
]
</script>

<template>
  <aside class="sidebar glass">
    <div class="logo">
      <div class="logo-icon">V</div>
      <span class="logo-text">VeriFlow</span>
    </div>
    
    <nav class="nav-menu">
      <button
        v-for="item in menuItems"
        :key="item.id"
        :class="['nav-item', { active: activeTab === item.id }]"
        @click="activeTab = item.id"
      >
        <component :is="item.icon" :size="20" />
        <span>{{ item.label }}</span>
      </button>
    </nav>
    
    <div class="sidebar-footer">
      <button class="nav-item">
        <Settings :size="20" />
        <span>Settings</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 220px;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px;
  border-radius: 0;
  border-right: 1px solid var(--color-border);
  border-top: none;
  border-bottom: none;
  border-left: none;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  margin-bottom: 24px;
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, var(--color-accent-purple), var(--color-accent-blue));
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  background: linear-gradient(135deg, var(--color-text-primary), var(--color-accent-purple));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  text-align: left;
  width: 100%;
}

.nav-item:hover {
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
}

.nav-item.active {
  background: rgba(139, 92, 246, 0.15);
  border-color: var(--color-border-accent);
  color: var(--color-accent-purple);
}

.sidebar-footer {
  border-top: 1px solid var(--color-border);
  padding-top: 12px;
}
</style>
