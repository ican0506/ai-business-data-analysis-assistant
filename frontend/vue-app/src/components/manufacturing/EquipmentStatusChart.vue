<script setup>
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({ data: { type: Array, default: () => [] } })
const chartElement = ref(null)
let chart

function renderChart() {
  if (!chartElement.value) return
  chart ||= echarts.init(chartElement.value)
  chart.setOption({
    color: ['#16a085', '#f2994a', '#e74c3c', '#829ab1'],
    tooltip: { trigger: 'item', formatter: '{b}: {c} 台 ({d}%)' },
    legend: { bottom: 0 },
    series: [{ type: 'pie', radius: ['42%', '68%'], avoidLabelOverlap: true, label: { formatter: '{b}\n{c} 台' }, data: props.data }],
  }, { notMerge: true })
}

function resizeChart() { chart?.resize() }
onMounted(() => { renderChart(); window.addEventListener('resize', resizeChart) })
watch(() => props.data, renderChart, { deep: true })
onBeforeUnmount(() => { window.removeEventListener('resize', resizeChart); chart?.dispose() })
</script>

<template><el-card class="chart-panel" shadow="never"><template #header><strong>设备状态分布</strong></template><div ref="chartElement" class="chart-canvas" aria-label="设备状态分布图" /></el-card></template>

<style scoped>
.chart-panel { border-color: #e7edf5; }
.chart-canvas { height: 320px; }
</style>
