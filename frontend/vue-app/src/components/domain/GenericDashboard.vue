<script setup>
import { computed } from 'vue'

import KpiCard from '../dashboard/KpiCard.vue'
import { formatNumber } from '../../utils/domainDisplay'

const props = defineProps({ metrics: { type: Object, required: true } })
const analysis = computed(() => props.metrics.generic_analysis || {})
const kpis = computed(() => [{ label: '数据行数', value: formatNumber(analysis.value.row_count ?? props.metrics.total_rows), suffix: '行', trend: '真实统计', type: 'primary' }, { label: '字段数量', value: formatNumber(analysis.value.column_profile?.length), suffix: '列', trend: '真实统计', type: 'info' }])
</script>

<template>
  <div class="kpi-grid"><KpiCard v-for="item in kpis" :key="item.label" :item="item" /></div>
  <div class="dashboard-grid domain-dashboard-grid">
    <el-card class="dashboard-panel" shadow="never"><template #header><strong>字段信息</strong></template><el-table :data="analysis.column_profile || []"><el-table-column prop="column" label="字段" /><el-table-column prop="dtype" label="数据类型" /><el-table-column prop="non_null_count" label="非空值数量" /><el-table-column prop="unique_count" label="唯一值数量" /></el-table></el-card>
    <el-card class="dashboard-panel" shadow="never"><template #header><strong>缺失值统计</strong></template><el-table :data="analysis.missing_value_analysis || []"><el-table-column prop="column" label="字段" /><el-table-column prop="missing_count" label="缺失数量" /><el-table-column prop="missing_ratio" label="缺失比例" /></el-table></el-card>
  </div>
</template>
