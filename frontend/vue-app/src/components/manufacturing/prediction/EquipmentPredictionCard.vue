<script setup>
defineProps({ prediction: { type: Object, required: true } })
</script>

<template>
  <el-card shadow="never" class="prediction-card">
    <template #header><strong>设备故障趋势预测</strong></template>
    <el-empty v-if="!(prediction || []).length" description="暂无设备预测结果" :image-size="56" />
    <div v-else class="prediction-list"><article v-for="item in prediction" :key="item.equipment_name || 'unknown'" class="equipment-row"><div><strong>{{ item.equipment_name || '未命名设备' }}</strong><p>{{ item.reasons?.join(' ') || '未触发设备风险规则。' }}</p></div><el-tag :type="item.risk_level === '高风险' ? 'danger' : item.risk_level === '中风险' ? 'warning' : 'success'">{{ item.risk_level }}</el-tag><div class="facts"><span>预测温度：{{ item.predicted_temperature ?? '—' }}</span><span>预测振动：{{ item.predicted_vibration ?? '—' }}</span></div><p class="suggestion">{{ item.maintenance_suggestion }}</p></article></div>
  </el-card>
</template>

<style scoped>
.prediction-card { height: 100%; }.prediction-list { display: grid; gap: 12px; }.equipment-row { display: grid; gap: 8px; padding: 14px; border: 1px solid #e4ecf5; border-radius: 8px; }.equipment-row > :nth-child(2) { justify-self: start; }.equipment-row strong { color: #173658; }.equipment-row p { margin: 0; color: #61758d; line-height: 1.65; }.facts { display: flex; flex-wrap: wrap; gap: 14px; color: #42617d; font-size: 13px; }.suggestion { color: #277458 !important; }
</style>
