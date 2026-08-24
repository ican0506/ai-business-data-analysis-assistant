<script setup>
defineProps({ analysis: { type: Object, default: () => ({}) }, diagnoses: { type: Array, default: () => [] } })
</script>

<template>
  <el-card shadow="never"><template #header><strong>设备分析</strong></template>
    <el-descriptions :column="4" border><el-descriptions-item label="设备数量">{{ analysis.equipment_count ?? '--' }}</el-descriptions-item><el-descriptions-item label="运行率">{{ analysis.running_rate ?? '--' }}<template v-if="analysis.running_rate !== null && analysis.running_rate !== undefined">%</template></el-descriptions-item><el-descriptions-item label="故障数量">{{ analysis.fault_count ?? '--' }}</el-descriptions-item><el-descriptions-item label="异常设备">{{ analysis.abnormal_equipment_count ?? '--' }}</el-descriptions-item></el-descriptions>
    <div v-if="diagnoses.length" class="diagnosis-list"><div v-for="item in diagnoses" :key="item.equipment_name" class="diagnosis-item"><el-tag :type="item.risk_level === '高风险' ? 'danger' : item.risk_level === '中风险' ? 'warning' : 'success'">{{ item.risk_level }}</el-tag><strong>{{ item.equipment_name }}</strong><span>{{ item.problem_analysis }}</span></div></div>
  </el-card>
</template>

<style scoped>.diagnosis-list { display: grid; gap: 10px; margin-top: 16px; }.diagnosis-item { display: flex; align-items: flex-start; gap: 10px; color: #486581; line-height: 1.6; }.diagnosis-item strong { color: #173658; white-space: nowrap; }</style>
