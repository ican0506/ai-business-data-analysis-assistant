<script setup>
import * as echarts from 'echarts'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  equipmentPredictions: { type: Array, default: () => [] },
  energyPrediction: { type: Object, default: null },
  productionPrediction: { type: Object, default: null },
})

const equipmentElement = ref(null)
const energyElement = ref(null)
const productionElement = ref(null)
let equipmentChart
let energyChart
let productionChart

function dispose(chart) { chart?.dispose() }
function numberOrNull(value) { const number = Number(value); return Number.isFinite(number) ? number : null }

async function renderCharts() {
  await nextTick()
  if (equipmentElement.value) {
    if (equipmentChart?.getDom() !== equipmentElement.value) dispose(equipmentChart)
    equipmentChart ||= echarts.init(equipmentElement.value)
    equipmentChart.setOption({
      color: ['#e76f51', '#457b9d'], tooltip: { trigger: 'axis' }, legend: { data: ['预测温度', '预测振动'], bottom: 0 }, grid: { left: 44, right: 22, top: 30, bottom: 46 },
      xAxis: { type: 'category', data: props.equipmentPredictions.map((item) => item.equipment_name || '未命名设备'), axisLabel: { color: '#627d98' } },
      yAxis: [{ type: 'value', name: '温度', axisLabel: { color: '#627d98' }, splitLine: { lineStyle: { color: '#edf2f7' } } }, { type: 'value', name: '振动', axisLabel: { color: '#627d98' } }],
      series: [
        { name: '预测温度', type: 'bar', data: props.equipmentPredictions.map((item) => numberOrNull(item.predicted_temperature)), barMaxWidth: 32 },
        { name: '预测振动', type: 'line', yAxisIndex: 1, smooth: true, data: props.equipmentPredictions.map((item) => numberOrNull(item.predicted_vibration)) },
      ],
    }, { notMerge: true })
  }
  if (energyElement.value) {
    if (energyChart?.getDom() !== energyElement.value) dispose(energyChart)
    energyChart ||= echarts.init(energyElement.value)
    energyChart.setOption({
      color: ['#16a085', '#f2994a'], tooltip: { trigger: 'axis' }, legend: { data: ['历史基线', '预测单位能耗'], bottom: 0 }, grid: { left: 44, right: 22, top: 30, bottom: 46 },
      xAxis: { type: 'category', data: ['单位能耗'], axisLabel: { color: '#627d98' } }, yAxis: { type: 'value', axisLabel: { color: '#627d98' }, splitLine: { lineStyle: { color: '#edf2f7' } } },
      series: [
        { name: '历史基线', type: 'bar', data: [numberOrNull(props.energyPrediction?.baseline_unit_energy_consumption)], barMaxWidth: 36 },
        { name: '预测单位能耗', type: 'bar', data: [numberOrNull(props.energyPrediction?.predicted_unit_energy_consumption)], barMaxWidth: 36 },
      ],
      graphic: { type: 'text', right: 18, top: 12, style: { text: `趋势：${props.energyPrediction?.trend || '—'}`, fill: '#54718e', fontSize: 12 } },
    }, { notMerge: true })
  }
  if (productionElement.value) {
    if (productionChart?.getDom() !== productionElement.value) dispose(productionChart)
    productionChart ||= echarts.init(productionElement.value)
    productionChart.setOption({
      color: ['#2f80ed', '#8e5ae8'], tooltip: { trigger: 'axis' }, legend: { data: ['当前完成率', '预测产量'], bottom: 0 }, grid: { left: 44, right: 22, top: 30, bottom: 46 },
      xAxis: { type: 'category', data: ['生产预测'], axisLabel: { color: '#627d98' } },
      yAxis: [{ type: 'value', name: '完成率', axisLabel: { color: '#627d98', formatter: '{value}%' }, splitLine: { lineStyle: { color: '#edf2f7' } } }, { type: 'value', name: '产量', axisLabel: { color: '#627d98' } }],
      series: [
        { name: '当前完成率', type: 'bar', data: [numberOrNull(props.productionPrediction?.completion_rate)], barMaxWidth: 36 },
        { name: '预测产量', type: 'bar', yAxisIndex: 1, data: [numberOrNull(props.productionPrediction?.predicted_output)], barMaxWidth: 36 },
      ],
      graphic: { type: 'text', right: 18, top: 12, style: { text: `延期风险：${props.productionPrediction?.delay_risk || '未设置目标日期'}`, fill: '#54718e', fontSize: 12 } },
    }, { notMerge: true })
  }
}

function resizeCharts() { equipmentChart?.resize(); energyChart?.resize(); productionChart?.resize() }

onMounted(() => { void renderCharts(); window.addEventListener('resize', resizeCharts) })
watch(() => [props.equipmentPredictions, props.energyPrediction, props.productionPrediction], () => { void renderCharts() }, { deep: true })
onBeforeUnmount(() => { window.removeEventListener('resize', resizeCharts); dispose(equipmentChart); dispose(energyChart); dispose(productionChart) })
</script>

<template>
  <div class="prediction-trend-grid">
    <el-card shadow="never"><template #header><strong>设备预测趋势</strong></template><div ref="equipmentElement" class="chart-canvas" aria-label="设备预测温度与振动图" /></el-card>
    <el-card shadow="never"><template #header><strong>单位能耗预测</strong></template><div ref="energyElement" class="chart-canvas" aria-label="单位能耗预测图" /></el-card>
    <el-card shadow="never"><template #header><strong>生产达成预测</strong></template><div ref="productionElement" class="chart-canvas" aria-label="生产达成预测图" /></el-card>
  </div>
</template>

<style scoped>
.prediction-trend-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; }.chart-canvas { height: 260px; } @media (max-width: 1180px) { .prediction-trend-grid { grid-template-columns: 1fr; } }
</style>
