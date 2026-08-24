<script setup>
import { computed } from 'vue'

const props = defineProps({ diagnosis: { type: Object, required: true } })

const tagType = computed(() => ({ 高风险: 'danger', 中风险: 'warning', 正常: 'success' }[props.diagnosis.risk_level] || 'info'))
</script>

<template>
  <div class="diagnosis-result">
    <el-card shadow="never">
      <template #header><div class="card-title"><span>诊断结论</span><el-tag :type="tagType" effect="light">{{ diagnosis.risk_level }}</el-tag></div></template>
      <p class="problem-analysis">{{ diagnosis.problem_analysis }}</p>
    </el-card>
    <div class="result-grid">
      <el-card shadow="never"><template #header>可能原因</template><ol><li v-for="item in diagnosis.possible_causes" :key="item">{{ item }}</li></ol></el-card>
      <el-card shadow="never"><template #header>处理建议</template><ol><li v-for="item in diagnosis.suggestions" :key="item">{{ item }}</li></ol></el-card>
    </div>
  </div>
</template>

<style scoped>
.diagnosis-result { display: grid; gap: 18px; }.card-title { display: flex; align-items: center; justify-content: space-between; color: #132d4e; font-weight: 700; }.problem-analysis { margin: 0; color: #344b66; font-size: 16px; line-height: 1.8; }.result-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }.result-grid ol { margin: 0; padding-left: 20px; color: #4f6480; line-height: 2; }@media (max-width: 760px) { .result-grid { grid-template-columns: 1fr; } }
</style>
