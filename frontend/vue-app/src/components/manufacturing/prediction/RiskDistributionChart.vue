<script setup>
import * as echarts from 'echarts'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({ distribution: { type: Array, default: () => [] } })
const element = ref(null)
let chart

async function renderChart() {
  await nextTick()
  if (!element.value) return
  if (chart?.getDom() !== element.value) chart?.dispose()
  chart ||= echarts.init(element.value)
  chart.setOption({
    color: ['#e76f51', '#f2b84b', '#2cad7c', '#8da3b8'], tooltip: { trigger: 'item' }, legend: { bottom: 0, textStyle: { color: '#627d98' } },
    series: [{ type: 'pie', radius: ['44%', '70%'], avoidLabelOverlap: true, label: { formatter: '{b}\n{c} 条', color: '#415a75' }, data: props.distribution }],
  }, { notMerge: true })
}
function resize() { chart?.resize() }
onMounted(() => { void renderChart(); window.addEventListener('resize', resize) })
watch(() => props.distribution, () => { void renderChart() }, { deep: true })
onBeforeUnmount(() => { window.removeEventListener('resize', resize); chart?.dispose() })
</script>

<template>
  <el-card shadow="never" class="risk-chart"><template #header><strong>预测风险分布</strong></template><div ref="element" class="chart-canvas" aria-label="预测风险分布图" /></el-card>
</template>

<style scoped>
.chart-canvas { height: 280px; }
</style>
