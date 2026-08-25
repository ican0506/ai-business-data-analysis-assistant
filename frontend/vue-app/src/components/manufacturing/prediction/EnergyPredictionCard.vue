<script setup>
defineProps({ prediction: { type: Object, required: true } })
</script>

<template>
  <el-card shadow="never" class="prediction-card">
    <template #header><strong>能耗趋势预测</strong></template>
    <el-empty v-if="!prediction || prediction.warning_level === '数据不足'" description="能耗有效历史数据不足，暂无法生成趋势预测。" :image-size="56" />
    <dl v-else class="metric-list"><div><dt>生产线</dt><dd>{{ prediction.production_line || '全厂' }}</dd></div><div><dt>预测单位能耗</dt><dd>{{ prediction.predicted_unit_energy_consumption ?? '—' }}</dd></div><div><dt>历史基线</dt><dd>{{ prediction.baseline_unit_energy_consumption ?? '—' }}</dd></div><div><dt>偏差率</dt><dd>{{ prediction.deviation_rate ?? '—' }}{{ prediction.deviation_rate === null ? '' : '%' }}</dd></div><div><dt>趋势</dt><dd>{{ prediction.trend || '—' }}</dd></div><div><dt>预警等级</dt><dd>{{ prediction.warning_level || '—' }}</dd></div></dl>
  </el-card>
</template>

<style scoped>
.prediction-card { height: 100%; }.metric-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 0; }.metric-list div { padding: 12px; border-radius: 8px; background: #f7faff; }.metric-list dt { color: #789; font-size: 12px; }.metric-list dd { margin: 6px 0 0; color: #163657; font-weight: 700; }@media (max-width: 500px) { .metric-list { grid-template-columns: 1fr; } }
</style>
