<script setup>
import { WarningFilled } from '@element-plus/icons-vue'

defineProps({ anomalies: { type: Array, default: () => [] }, problems: { type: Array, default: () => [] } })
</script>

<template>
  <el-card class="report-panel risk-panel" shadow="never">
    <template #header><div class="report-panel-title"><span>02</span><div><strong>异常分析</strong><small>异常指标与风险提示</small></div></div></template>
    <div class="report-list"><div v-for="item in anomalies" :key="item" class="report-list-item warning"><el-icon><WarningFilled /></el-icon><span>{{ item }}</span></div></div>
    <el-divider content-position="left">业务风险研判</el-divider>
    <ul class="insight-list"><li v-for="item in problems" :key="item">{{ item }}</li></ul>
  </el-card>
</template>
