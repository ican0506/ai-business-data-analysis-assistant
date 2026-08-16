<script setup>
import { computed } from 'vue'

import BarChart from '../analysis/BarChart.vue'
import LineChart from '../analysis/LineChart.vue'
import KpiCard from '../dashboard/KpiCard.vue'
import { formatNumber } from '../../utils/domainDisplay'

const props = defineProps({ metrics: { type: Object, required: true } })
const analysis = computed(() => props.metrics.inventory_analysis || {})
const kpis = computed(() => {
  const stock = analysis.value.stock_summary
  const value = analysis.value.inventory_value
  return [
    analysis.value.inventory_count !== null && analysis.value.inventory_count !== undefined ? { label: '商品数量', value: formatNumber(analysis.value.inventory_count), suffix: '个', trend: '真实统计', type: 'primary' } : null,
    stock ? { label: '库存总量', value: formatNumber(stock.total), suffix: '', trend: '真实统计', type: 'success' } : null,
    stock ? { label: '平均库存', value: formatNumber(stock.average), suffix: '', trend: '真实统计', type: 'info' } : null,
    stock ? { label: '最大库存', value: formatNumber(stock.maximum), suffix: '', trend: '真实统计', type: 'warning' } : null,
    stock ? { label: '最小库存', value: formatNumber(stock.minimum), suffix: '', trend: '真实统计', type: 'warning' } : null,
    value ? { label: '库存价值', value: formatNumber(value.total), suffix: '', trend: '真实统计', type: 'success' } : null,
  ].filter(Boolean)
})
</script>

<template>
  <div class="kpi-grid"><KpiCard v-for="item in kpis" :key="item.label" :item="item" /></div>
  <div class="dashboard-grid domain-dashboard-grid">
    <el-card v-if="analysis.category_stock?.length" class="dashboard-panel" shadow="never"><template #header><strong>分类库存</strong></template><BarChart title="库存数量" :data="analysis.category_stock" /></el-card>
    <el-card v-if="analysis.warehouse_stock?.length" class="dashboard-panel" shadow="never"><template #header><strong>仓库库存</strong></template><BarChart title="库存数量" :data="analysis.warehouse_stock" /></el-card>
    <el-card v-if="analysis.inventory_trend?.length" class="dashboard-panel" shadow="never"><template #header><strong>库存趋势</strong></template><LineChart title="库存数量" :data="analysis.inventory_trend" /></el-card>
  </div>
  <div class="dashboard-grid domain-dashboard-grid">
    <el-card v-if="analysis.low_stock_analysis?.length" class="dashboard-panel" shadow="never"><template #header><strong>低库存商品</strong></template><el-table :data="analysis.low_stock_analysis"><el-table-column prop="product_id" label="商品编号" /><el-table-column prop="product_name" label="商品名称" /><el-table-column prop="stock_quantity" label="当前库存" /><el-table-column prop="safety_stock" label="安全库存" /><el-table-column prop="shortage" label="库存缺口" /></el-table></el-card>
    <el-card v-if="analysis.supplier_stock?.length" class="dashboard-panel" shadow="never"><template #header><strong>供应商库存</strong></template><el-table :data="analysis.supplier_stock" size="small"><el-table-column prop="name" label="供应商" /><el-table-column prop="value" label="库存数量" /></el-table></el-card>
    <el-card v-if="analysis.inventory_flow" class="dashboard-panel" shadow="never"><template #header><strong>库存流动</strong></template><el-descriptions :column="3" border><el-descriptions-item label="入库总量">{{ analysis.inventory_flow.inbound_total }}</el-descriptions-item><el-descriptions-item label="出库总量">{{ analysis.inventory_flow.outbound_total }}</el-descriptions-item><el-descriptions-item label="净变化">{{ analysis.inventory_flow.net_change }}</el-descriptions-item></el-descriptions></el-card>
  </div>
</template>
