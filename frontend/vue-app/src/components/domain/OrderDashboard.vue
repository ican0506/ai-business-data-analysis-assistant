<script setup>
import { computed } from 'vue'

import BarChart from '../analysis/BarChart.vue'
import LineChart from '../analysis/LineChart.vue'
import KpiCard from '../dashboard/KpiCard.vue'
import { formatNumber } from '../../utils/domainDisplay'

const props = defineProps({ metrics: { type: Object, required: true } })
const orderAnalysis = computed(() => props.metrics.order_analysis || {})
const overview = computed(() => orderAnalysis.value.overview || {})
const timeAnalysis = computed(() => orderAnalysis.value.time_analysis || {})
const customerAnalysis = computed(() => orderAnalysis.value.customer_analysis || null)
const statusSummary = computed(() => orderAnalysis.value.status_summary || null)
const quality = computed(() => orderAnalysis.value.data_quality || null)

const kpis = computed(() => [
  overview.value.order_count !== null && overview.value.order_count !== undefined
    ? { label: '订单数量', value: formatNumber(overview.value.order_count), suffix: '笔', trend: '去重订单', type: 'primary' } : null,
  overview.value.sales_total !== null && overview.value.sales_total !== undefined
    ? { label: '已验证销售额', value: formatNumber(overview.value.sales_total), suffix: '', trend: '可验证订单金额', type: 'success' } : null,
  overview.value.average_order_value !== null && overview.value.average_order_value !== undefined
    ? { label: '已验证平均客单价', value: formatNumber(overview.value.average_order_value), suffix: '', trend: '已验证订单', type: 'warning' } : null,
  customerAnalysis.value?.unique_customer_count !== null && customerAnalysis.value?.unique_customer_count !== undefined
    ? { label: '客户数量', value: formatNumber(customerAnalysis.value.unique_customer_count), suffix: '位', trend: '按客户编号去重', type: 'primary' } : null,
  customerAnalysis.value?.repeat_customer_rate !== null && customerAnalysis.value?.repeat_customer_rate !== undefined
    ? { label: '复购率', value: formatNumber(customerAnalysis.value.repeat_customer_rate), suffix: '%', trend: '复购客户占比', type: 'success' } : null,
  statusSummary.value?.refund_rate !== null && statusSummary.value?.refund_rate !== undefined
    ? { label: '退款率', value: formatNumber(statusSummary.value.refund_rate), suffix: '%', trend: '有效状态订单', type: 'danger' } : null,
].filter(Boolean))

const qualityWarnings = computed(() => {
  if (!quality.value) return []
  const labels = {
    duplicate_row_count: '重复记录', duplicate_order_id_count: '重复订单号', invalid_date_count: '无效日期',
    invalid_unit_price_count: '异常单价', invalid_quantity_count: '异常数量', invalid_discount_count: '异常折扣', amount_mismatch_count: '金额不一致',
    phone_invalid_count: '无效联系方式', email_invalid_count: '无效邮箱', phone_missing_count: '联系方式缺失', email_missing_count: '邮箱缺失', unverified_order_count: '无法验证金额订单',
  }
  return Object.entries(labels).flatMap(([key, label]) => Number(quality.value[key]) > 0 ? [`${label} ${quality.value[key]} 条`] : [])
})
</script>

<template>
  <div class="kpi-grid"><KpiCard v-for="item in kpis" :key="item.label" :item="item" /></div>
  <el-alert v-if="overview.amount_mismatch_count > 0" class="quality-alert" title="检测到订单金额与单价 × 数量 × 折扣不一致，销售统计已优先使用可验证的计算金额。" type="warning" :closable="false" show-icon />
  <el-alert v-if="overview.unverified_order_count > 0" class="quality-alert" :title="`存在 ${overview.unverified_order_count} 笔订单金额无法通过单价 × 数量 × 折扣验证，未计入已验证销售额。`" type="warning" :closable="false" show-icon />
  <div class="dashboard-grid domain-dashboard-grid">
    <el-card v-if="orderAnalysis.product_analysis?.length" class="dashboard-panel" shadow="never"><template #header><strong>商品销售排行</strong></template><BarChart title="商品已验证销售额" :data="orderAnalysis.product_analysis.map(item => ({ name: item.name, value: item.sales_amount }))" /></el-card>
    <el-card v-if="orderAnalysis.category_analysis?.length" class="dashboard-panel" shadow="never"><template #header><strong>品类销售排行</strong></template><BarChart title="品类已验证销售额" :data="orderAnalysis.category_analysis.map(item => ({ name: item.category, value: item.sales_amount }))" /></el-card>
    <el-card v-if="metrics.top_regions?.length" class="dashboard-panel" shadow="never"><template #header><strong>地区销售表现</strong></template><BarChart title="地区已验证销售额" :data="metrics.top_regions" /></el-card>
    <el-card v-if="timeAnalysis.monthly_sales_trend?.length" class="dashboard-panel" shadow="never"><template #header><strong>月度已验证销售额趋势</strong></template><LineChart title="月度已验证销售额" :data="timeAnalysis.monthly_sales_trend" /></el-card>
    <el-card v-if="orderAnalysis.status_analysis?.length" class="dashboard-panel" shadow="never"><template #header><strong>订单状态分布</strong></template><BarChart title="状态订单数" :data="orderAnalysis.status_analysis.map(item => ({ name: item.name, value: item.order_count }))" /></el-card>
    <el-card v-if="orderAnalysis.payment_method_analysis?.length" class="dashboard-panel" shadow="never"><template #header><strong>支付方式分布</strong></template><BarChart title="支付方式已验证销售额" :data="orderAnalysis.payment_method_analysis.map(item => ({ name: item.name, value: item.sales_amount }))" /></el-card>
  </div>
  <div class="dashboard-grid domain-dashboard-grid">
    <el-card v-if="customerAnalysis?.top_customers?.length" class="dashboard-panel" shadow="never"><template #header><strong>Top 客户</strong></template><el-table :data="customerAnalysis.top_customers" size="small"><el-table-column prop="customer_id" label="客户编号" /><el-table-column prop="order_count" label="订单数" /><el-table-column prop="sales_amount" label="已验证销售额" /></el-table></el-card>
    <el-card v-if="metrics.region_performance?.length" class="dashboard-panel" shadow="never"><template #header><strong>地区订单表现</strong></template><el-table :data="metrics.region_performance" size="small"><el-table-column prop="name" label="地区" /><el-table-column prop="sales_amount" label="已验证销售额" /><el-table-column prop="completion_rate" label="目标完成率"><template #default="{ row }">{{ row.completion_rate === null ? '—' : `${row.completion_rate}%` }}</template></el-table-column></el-table></el-card>
    <el-card v-if="quality" class="dashboard-panel" shadow="never"><template #header><strong>数据质量</strong></template><el-empty v-if="!qualityWarnings.length" description="当前未发现已统计的质量异常" :image-size="56" /><el-tag v-for="warning in qualityWarnings" :key="warning" class="quality-tag" type="warning" effect="plain">{{ warning }}</el-tag></el-card>
  </div>
</template>

<style scoped>
.quality-alert { margin: 16px 0; }
.quality-tag { margin: 0 8px 8px 0; }
</style>
