<script setup>
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({ data: { type: Object, required: true } })
const chartElement = ref(null)
let chart
function renderChart() {
  chart ||= echarts.init(chartElement.value)
  chart.setOption({
    grid: { left: 36, right: 16, top: 28, bottom: 28 }, tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: props.data.labels, axisTick: { show: false }, axisLine: { lineStyle: { color: '#d9e2ec' } }, axisLabel: { color: '#829ab1' } },
    yAxis: { type: 'value', max: 100, splitLine: { lineStyle: { color: '#f0f4f8' } }, axisLabel: { color: '#829ab1', formatter: '{value}%' } },
    series: [{ type: 'bar', data: props.data.values, barWidth: 28, itemStyle: { borderRadius: [6, 6, 0, 0], color: '#16a085' } }],
  })
}
function resizeChart() { chart?.resize() }
onMounted(() => { renderChart(); window.addEventListener('resize', resizeChart) })
watch(() => props.data, renderChart, { deep: true })
onBeforeUnmount(() => { window.removeEventListener('resize', resizeChart); chart?.dispose() })
</script>

<template><div ref="chartElement" class="chart-canvas" aria-label="指标柱状图" /></template>
