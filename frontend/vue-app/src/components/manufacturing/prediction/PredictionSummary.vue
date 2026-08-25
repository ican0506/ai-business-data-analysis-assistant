<script setup>
import { computed } from 'vue'

const props = defineProps({ prediction: { type: Object, required: true } })

const riskTagType = computed(() => ({ 高风险: 'danger', 中风险: 'warning', 正常: 'success', 数据不足: 'info' }[props.prediction.risk_level] || 'info'))
const typeName = computed(() => ({ equipment_risk: '设备故障趋势预测', energy_consumption: '能耗趋势预测', production_completion: '生产达成预测' }[props.prediction.prediction_type] || props.prediction.prediction_type))
</script>

<template>
  <el-card shadow="never" class="prediction-summary">
    <div class="summary-heading"><div><p class="eyebrow">PREDICTION SNAPSHOT</p><h3>{{ typeName }}</h3></div><el-tag :type="riskTagType" effect="light">{{ prediction.risk_level || '—' }}</el-tag></div>
    <div class="summary-meta"><span>对象：{{ prediction.scope_name || '全厂' }}</span><span>生成时间：{{ prediction.generated_at?.replace('T', ' ') || '—' }}</span><span>算法：{{ prediction.algorithm_version || 'deterministic-v1' }}</span></div>
  </el-card>
</template>

<style scoped>
.prediction-summary { border: 1px solid #dce7f5; }.summary-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }.eyebrow { margin: 0; color: #397af2; font-size: 12px; font-weight: 700; letter-spacing: 1.2px; }.summary-heading h3 { margin: 7px 0 0; color: #132d4e; font-size: 22px; }.summary-meta { display: flex; flex-wrap: wrap; gap: 12px 22px; margin-top: 18px; color: #6b7f99; font-size: 13px; }
</style>
