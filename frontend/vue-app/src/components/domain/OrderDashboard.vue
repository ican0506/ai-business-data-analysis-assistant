<script setup>
import { computed } from 'vue'

import BarChart from '../analysis/BarChart.vue'
import LineChart from '../analysis/LineChart.vue'
import KpiCard from '../dashboard/KpiCard.vue'
import { formatNumber } from '../../utils/domainDisplay'

const props = defineProps({ metrics: { type: Object, required: true } })
const kpis = computed(() => [
  props.metrics.order_count !== null && props.metrics.order_count !== undefined ? { label: '订单数量', value: formatNumber(props.metrics.order_count), suffix: '笔', trend: '真实统计', type: 'primary' } : null,
  props.metrics.sales_amount ? { label: '销售总额', value: formatNumber(props.metrics.sales_amount.total), suffix: '', trend: '真实统计', type: 'success' } : null,
  props.metrics.growth_rate !== null && props.metrics.growth_rate !== undefined ? { label: '增长率', value: formatNumber(props.metrics.growth_rate), suffix: '%', trend: '后端计算', type: props.metrics.growth_rate < 0 ? 'danger' : 'success' } : null,
  props.metrics.completion_rate !== null && props.metrics.completion_rate !== undefined ? { label: '目标完成率', value: formatNumber(props.metrics.completion_rate), suffix: '%', trend: '后端计算', type: 'warning' } : null,
].filter(Boolean))
</script>

<template>
  <div class="kpi-grid"><KpiCard v-for="item in kpis" :key="item.label" :item="item" /></div>
  <div class="dashboard-grid domain-dashboard-grid">
    <el-card v-if="metrics.top_regions?.length" class="dashboard-panel" shadow="never"><template #header><strong>区域销售表现</strong></template><BarChart title="区域销售额" :data="metrics.top_regions" /></el-card>
    <el-card v-if="metrics.product_quantity?.length" class="dashboard-panel" shadow="never"><template #header><strong>商品销量排名</strong></template><BarChart title="商品销量" :data="metrics.product_quantity" /></el-card>
    <el-card v-if="metrics.region_performance?.length" class="dashboard-panel" shadow="never"><template #header><strong>区域目标完成情况</strong></template><el-table :data="metrics.region_performance" size="small"><el-table-column prop="name" label="区域" /><el-table-column prop="sales_amount" label="销售额" /><el-table-column prop="completion_rate" label="完成率"><template #default="{ row }">{{ row.completion_rate === null ? '—' : `${row.completion_rate}%` }}</template></el-table-column></el-table></el-card>
  </div>
</template>
