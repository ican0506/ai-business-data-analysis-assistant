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
    color: ['#9b51e0'],
    tooltip: { trigger: 'axis' },
    grid: { left: 54, right: 22, top: 34, bottom: 34 },
    xAxis: { type: 'category', data: props.data.map((item) => item.date), axisLabel: { color: '#6b7f99' } },
    yAxis: { type: 'value', name: '单位能耗', axisLabel: { color: '#6b7f99' }, splitLine: { lineStyle: { color: '#edf2f7' } } },
    series: [{ name: '单位能耗', type: 'line', smooth: true, symbolSize: 7, data: props.data.map((item) => item.unit_energy_consumption), areaStyle: { opacity: 0.1 } }],
  }, { notMerge: true })
}

function resizeChart() { chart?.resize() }
onMounted(() => { renderChart(); window.addEventListener('resize', resizeChart) })
watch(() => props.data, renderChart, { deep: true })
onBeforeUnmount(() => { window.removeEventListener('resize', resizeChart); chart?.dispose() })
</script>

<template><el-card class="chart-panel" shadow="never"><template #header><strong>单位能耗趋势</strong></template><div ref="chartElement" class="chart-canvas" aria-label="能耗趋势图" /></el-card></template>

<style scoped>
.chart-panel { border-color: #e7edf5; }
.chart-canvas { height: 320px; }
</style>
