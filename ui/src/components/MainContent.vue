<script setup lang="ts">
</script>

<template>
  <main class="main-content">
    <header class="header glass">
      <h1>Welcome to VeriFlow</h1>
      <p class="subtitle">Upload a research paper to begin verification</p>
    </header>
    
    <div class="content-area">
      <div class="upload-zone glass glass-hover">
        <div class="upload-icon">📄</div>
        <h2>Drop your PDF here</h2>
        <p>or click to browse files</p>
      </div>
    </div>
  </main>
</template>

<style scoped>
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 24px;
  overflow: auto;
}

.header {
  padding: 24px;
  margin-bottom: 24px;
}

.header h1 {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 8px;
  background: linear-gradient(135deg, var(--color-text-primary), var(--color-accent-purple));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  color: var(--color-text-secondary);
  font-size: 14px;
}

.content-area {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-zone {
  width: 100%;
  max-width: 500px;
  padding: 60px 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-zone:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(139, 92, 246, 0.15);
}

.upload-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.upload-zone h2 {
  font-size: 20px;
  font-weight: 500;
  margin-bottom: 8px;
  color: var(--color-text-primary);
}

.upload-zone p {
  color: var(--color-text-secondary);
  font-size: 14px;
}
</style>
