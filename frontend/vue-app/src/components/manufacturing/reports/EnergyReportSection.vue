<script setup>
defineProps({ analysis: { type: Object, default: () => ({}) } })
</script>

<template>
  <el-card shadow="never"><template #header><strong>能源分析</strong></template>
    <el-descriptions :column="3" border><el-descriptions-item label="平均单位能耗">{{ analysis.average_unit_energy_consumption ?? '--' }}</el-descriptions-item><el-descriptions-item label="总电耗">{{ analysis.electricity_consumption_total ?? '--' }}</el-descriptions-item><el-descriptions-item label="总煤耗">{{ analysis.coal_consumption_total ?? '--' }}</el-descriptions-item></el-descriptions>
    <el-table v-if="analysis.energy_trend?.length" :data="analysis.energy_trend" class="section-table"><el-table-column prop="date" label="日期" /><el-table-column prop="electricity_consumption" label="电耗" /><el-table-column prop="coal_consumption" label="煤耗" /><el-table-column prop="average_unit_energy_consumption" label="平均单位能耗" /></el-table>
  </el-card>
</template>

<style scoped>.section-table { width: 100%; margin-top: 16px; }</style>
