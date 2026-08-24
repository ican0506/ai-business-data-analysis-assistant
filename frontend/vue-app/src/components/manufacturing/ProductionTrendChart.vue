<script setup>
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  trend: { type: Array, default: () => [] },
  lineComparison: { type: Array, default: () => [] },
})

const trendElement = ref(null)
const comparisonElement = ref(null)
let trendChart
let comparisonChart

function renderCharts() {
  if (!trendElement.value || !comparisonElement.value) return
  trendChart ||= echarts.init(trendElement.value)
  comparisonChart ||= echarts.init(comparisonElement.value)
  trendChart.setOption({
    color: ['#2f80ed', '#16a085'],
    tooltip: { trigger: 'axis' },
    legend: { data: ['熟料产量', '水泥产量'], bottom: 0 },
    grid: { left: 54, right: 22, top: 34, bottom: 46 },
    xAxis: { type: 'category', data: props.trend.map((item) => item.date), axisLabel: { color: '#6b7f99' } },
    yAxis: { type: 'value', name: '吨', axisLabel: { color: '#6b7f99' }, splitLine: { lineStyle: { color: '#edf2f7' } } },
    series: [
      { name: '熟料产量', type: 'line', smooth: true, data: props.trend.map((item) => item.clinker_output), areaStyle: { opacity: 0.08 } },
      { name: '水泥产量', type: 'line', smooth: true, data: props.trend.map((item) => item.cement_output), areaStyle: { opacity: 0.08 } },
    ],
  }, { notMerge: true })
  comparisonChart.setOption({
    color: ['#f2994a', '#2f80ed'],
    tooltip: { trigger: 'axis' },
    legend: { data: ['熟料产量', '水泥产量'], bottom: 0 },
    grid: { left: 54, right: 22, top: 34, bottom: 46 },
    xAxis: { type: 'category', data: props.lineComparison.map((item) => item.production_line), axisLabel: { color: '#6b7f99' } },
    yAxis: { type: 'value', name: '吨', axisLabel: { color: '#6b7f99' }, splitLine: { lineStyle: { color: '#edf2f7' } } },
    series: [
      { name: '熟料产量', type: 'bar', barMaxWidth: 34, data: props.lineComparison.map((item) => item.clinker_output) },
      { name: '水泥产量', type: 'bar', barMaxWidth: 34, data: props.lineComparison.map((item) => item.cement_output) },
    ],
  }, { notMerge: true })
}

function resizeCharts() { trendChart?.resize(); comparisonChart?.resize() }
onMounted(() => { renderCharts(); window.addEventListener('resize', resizeCharts) })
watch(() => [props.trend, props.lineComparison], renderCharts, { deep: true })
onBeforeUnmount(() => { window.removeEventListener('resize', resizeCharts); trendChart?.dispose(); comparisonChart?.dispose() })
</script>

<template>
  <div class="production-charts">
    <el-card class="chart-panel" shadow="never"><template #header><strong>生产趋势</strong></template><div ref="trendElement" class="chart-canvas" aria-label="生产趋势图" /></el-card>
    <el-card class="chart-panel" shadow="never"><template #header><strong>生产线对比</strong></template><div ref="comparisonElement" class="chart-canvas" aria-label="生产线对比柱状图" /></el-card>
  </div>
</template>

<style scoped>
.production-charts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.chart-panel { border-color: #e7edf5; }
.chart-canvas { height: 320px; }
@media (max-width: 900px) { .production-charts { grid-template-columns: 1fr; } }
</style>
