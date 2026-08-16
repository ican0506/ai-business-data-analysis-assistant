<script setup>
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
const props = defineProps({ title: { type: String, required: true }, data: { type: Array, default: () => [] } })
const element = ref(null); let chart
function render() { if (!element.value || !props.data.length) return; chart ||= echarts.init(element.value); chart.setOption({ tooltip: { trigger: 'axis' }, grid: { left: 42, right: 16, top: 32, bottom: 44 }, xAxis: { type: 'category', boundaryGap: false, data: props.data.map((item) => item.name), axisLabel: { color: '#627d98' } }, yAxis: { type: 'value', axisLabel: { color: '#627d98' }, splitLine: { lineStyle: { color: '#edf2f7' } } }, series: [{ name: props.title, type: 'line', smooth: true, data: props.data.map((item) => item.value ?? item.average), lineStyle: { color: '#16a085', width: 3 }, itemStyle: { color: '#16a085' }, areaStyle: { color: 'rgba(22,160,133,.12)' } }] }) }
function resize() { chart?.resize() }
onMounted(() => { render(); window.addEventListener('resize', resize) })
watch(() => props.data, render, { deep: true })
onBeforeUnmount(() => { window.removeEventListener('resize', resize); chart?.dispose() })
</script>
<template><div v-if="data.length" ref="element" class="chart-canvas" :aria-label="title" /><el-empty v-else :image-size="52" description="暂无可用图表数据" /></template>
