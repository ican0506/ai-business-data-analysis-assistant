<script setup>
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({ data: { type: Array, required: true } })
const chartElement = ref(null)
let chart
function renderChart() {
  chart ||= echarts.init(chartElement.value)
  chart.setOption({
    color: ['#2f80ed', '#16a085', '#f2994a', '#9b51e0'],
    tooltip: { trigger: 'item', formatter: '{b}<br/>{c}%（{d}%）' },
    legend: { bottom: 0, icon: 'circle', textStyle: { color: '#627d98' } },
    series: [{ type: 'pie', radius: ['48%', '72%'], center: ['50%', '43%'], avoidLabelOverlap: false, itemStyle: { borderColor: '#fff', borderWidth: 3 }, label: { show: false }, data: props.data }],
  })
}
function resizeChart() { chart?.resize() }
onMounted(() => { renderChart(); window.addEventListener('resize', resizeChart) })
watch(() => props.data, renderChart, { deep: true })
onBeforeUnmount(() => { window.removeEventListener('resize', resizeChart); chart?.dispose() })
</script>

<template><div ref="chartElement" class="chart-canvas" aria-label="数据分布饼图" /></template>
