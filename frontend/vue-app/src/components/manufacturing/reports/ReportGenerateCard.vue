<script setup>
defineProps({ loading: Boolean })
defineEmits(['generate'])
</script>

<template>
  <el-card class="generate-card" shadow="never">
    <div><p class="eyebrow">MANAGEMENT REPORT</p><h3>生成经营报告快照</h3><p>将当前生产、设备、能源指标与 AI 经营总结保存为不可变报告。</p></div>
    <el-button type="primary" :loading="loading" :disabled="loading" @click="$emit('generate')">生成经营报告</el-button>
  </el-card>
</template>

<style scoped>
.generate-card { display: flex; justify-content: space-between; align-items: center; border-color: #dbe6f3; }.generate-card :deep(.el-card__body) { display: flex; justify-content: space-between; align-items: center; gap: 20px; width: 100%; }.eyebrow { margin: 0; color: #2f74e8; font-weight: 700; font-size: 12px; letter-spacing: .1em; }.generate-card h3 { margin: 6px 0; color: #173658; }.generate-card p:not(.eyebrow) { margin: 0; color: #6b7f99; } @media (max-width: 680px) { .generate-card :deep(.el-card__body) { align-items: flex-start; flex-direction: column; } }
</style>
