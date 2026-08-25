<script setup>
defineProps({ prediction: { type: Object, required: true } })
</script>

<template>
  <el-card shadow="never" class="prediction-card">
    <template #header><strong>生产达成预测</strong></template>
    <el-empty v-if="!prediction || prediction.trend === '数据不足'" description="生产有效历史数据不足，暂无法生成达成预测。" :image-size="56" />
    <dl v-else class="metric-list"><div><dt>生产线</dt><dd>{{ prediction.production_line || '全厂' }}</dd></div><div><dt>当前完成率</dt><dd>{{ prediction.completion_rate ?? '—' }}{{ prediction.completion_rate === null ? '' : '%' }}</dd></div><div><dt>预测产量</dt><dd>{{ prediction.predicted_output ?? '—' }}</dd></div><div><dt>产量趋势</dt><dd>{{ prediction.trend || '—' }}</dd></div><div><dt>延期风险</dt><dd>{{ prediction.delay_risk || '未设置目标日期' }}</dd></div></dl>
  </el-card>
</template>

<style scoped>
.prediction-card { height: 100%; }.metric-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 0; }.metric-list div { padding: 12px; border-radius: 8px; background: #f7faff; }.metric-list dt { color: #789; font-size: 12px; }.metric-list dd { margin: 6px 0 0; color: #163657; font-weight: 700; }@media (max-width: 500px) { .metric-list { grid-template-columns: 1fr; } }
</style>
