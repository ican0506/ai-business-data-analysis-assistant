<script setup>
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({ data: { type: Object, required: true } })
const chartElement = ref(null)
let chart

function renderChart() {
  chart ||= echarts.init(chartElement.value)
  chart.setOption({
    grid: { left: 36, right: 20, top: 28, bottom: 28 },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: props.data.labels, boundaryGap: false, axisLine: { lineStyle: { color: '#d9e2ec' } }, axisLabel: { color: '#829ab1' } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f0f4f8' } }, axisLabel: { color: '#829ab1' } },
    series: [{ type: 'line', data: props.data.values, smooth: true, symbolSize: 7, lineStyle: { color: '#2f80ed', width: 3 }, itemStyle: { color: '#2f80ed' }, areaStyle: { color: 'rgba(47,128,237,.12)' } }],
  })
}

function resizeChart() { chart?.resize() }
onMounted(() => { renderChart(); window.addEventListener('resize', resizeChart) })
watch(() => props.data, renderChart, { deep: true })
onBeforeUnmount(() => { window.removeEventListener('resize', resizeChart); chart?.dispose() })
</script>

<template><div ref="chartElement" class="chart-canvas" aria-label="数据趋势折线图" /></template>
