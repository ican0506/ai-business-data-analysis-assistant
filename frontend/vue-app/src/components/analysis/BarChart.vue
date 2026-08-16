<script setup>
import * as echarts from 'echarts'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
const props = defineProps({ title: { type: String, required: true }, data: { type: Array, default: () => [] } })
const element = ref(null); let chart
function dispose() { chart?.dispose(); chart = undefined }
async function render() { if (!props.data.length) { dispose(); return }; await nextTick(); if (!element.value) return; if (chart?.getDom() !== element.value) dispose(); chart ||= echarts.init(element.value); chart.setOption({ tooltip: { trigger: 'axis' }, grid: { left: 42, right: 16, top: 32, bottom: 48 }, xAxis: { type: 'category', data: props.data.map((item) => item.name), axisLabel: { color: '#627d98', rotate: 22 } }, yAxis: { type: 'value', axisLabel: { color: '#627d98' }, splitLine: { lineStyle: { color: '#edf2f7' } } }, series: [{ name: props.title, type: 'bar', data: props.data.map((item) => item.value), barMaxWidth: 36, itemStyle: { color: '#2f80ed', borderRadius: [5, 5, 0, 0] } }] }) }
function resize() { chart?.resize() }
onMounted(() => { render(); window.addEventListener('resize', resize) })
watch(() => props.data, render, { deep: true })
onBeforeUnmount(() => { window.removeEventListener('resize', resize); dispose() })
</script>
<template><div v-if="data.length" ref="element" class="chart-canvas" :aria-label="title" /><el-empty v-else :image-size="52" description="暂无可用图表数据" /></template>
