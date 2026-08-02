<script setup>
import { Loading } from '@element-plus/icons-vue'
</script>

<template>
  <div class="analysis-loading" aria-live="polite">
    <el-skeleton :rows="8" animated />
    <div class="loading-copy"><el-icon class="is-loading"><Loading /></el-icon><span>AI 正在解读业务数据，请稍候…</span></div>
  </div>
</template>
