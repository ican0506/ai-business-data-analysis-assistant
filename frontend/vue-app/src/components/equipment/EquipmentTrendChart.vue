<script setup>
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  metric: { type: String, required: true },
  unit: { type: String, default: '' },
  color: { type: String, default: '#2f6fed' },
  records: { type: Array, default: () => [] },
})

const chartElement = ref(null)
let chart

function renderChart() {
  if (!chartElement.value) return
  chart ||= echarts.init(chartElement.value)
  chart.setOption({
    color: [props.color],
    grid: { left: 48, right: 28, top: 32, bottom: 40 },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: props.records.map((item) => item.date), boundaryGap: false },
    yAxis: { type: 'value', name: props.unit },
    series: [{ name: props.title, type: 'line', smooth: true, data: props.records.map((item) => item[props.metric]), areaStyle: { opacity: 0.12 } }],
  }, { notMerge: true })
}

function resizeChart() { chart?.resize() }
onMounted(() => { renderChart(); window.addEventListener('resize', resizeChart) })
watch(() => [props.records, props.metric], renderChart, { deep: true })
onBeforeUnmount(() => { window.removeEventListener('resize', resizeChart); chart?.dispose() })
</script>

<template>
  <el-card shadow="never" class="trend-panel">
    <template #header><strong>{{ title }}</strong></template>
    <div ref="chartElement" class="chart-canvas" :aria-label="`${title}图`" />
  </el-card>
</template>

<style scoped>
.trend-panel { border-color: #e7edf5; }
.chart-canvas { height: 280px; }
</style>
