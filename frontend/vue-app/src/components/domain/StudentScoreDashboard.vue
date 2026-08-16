<script setup>
import { computed } from 'vue'

import BarChart from '../analysis/BarChart.vue'
import LineChart from '../analysis/LineChart.vue'
import KpiCard from '../dashboard/KpiCard.vue'
import { formatNumber } from '../../utils/domainDisplay'

const props = defineProps({ metrics: { type: Object, required: true } })
const analysis = computed(() => props.metrics.student_score_analysis || {})
const kpis = computed(() => {
  const summary = analysis.value.score_summary
  return [
    analysis.value.student_count !== null && analysis.value.student_count !== undefined ? { label: '学生数量', value: formatNumber(analysis.value.student_count), suffix: '人', trend: '真实统计', type: 'primary' } : null,
    summary ? { label: '平均分', value: formatNumber(summary.average), suffix: '分', trend: '真实统计', type: 'success' } : null,
    summary ? { label: '最高分', value: formatNumber(summary.maximum), suffix: '分', trend: '真实统计', type: 'warning' } : null,
    summary ? { label: '最低分', value: formatNumber(summary.minimum), suffix: '分', trend: '真实统计', type: 'info' } : null,
    summary ? { label: '中位数', value: formatNumber(summary.median), suffix: '分', trend: '真实统计', type: 'primary' } : null,
  ].filter(Boolean)
})
const subjectBars = computed(() => (analysis.value.subject_score || []).map((item) => ({ name: item.name, value: item.average })))
const classBars = computed(() => (analysis.value.class_score || []).map((item) => ({ name: item.name, value: item.average })))
</script>

<template>
  <div class="kpi-grid"><KpiCard v-for="item in kpis" :key="item.label" :item="item" /></div>
  <div class="dashboard-grid domain-dashboard-grid">
    <el-card v-if="subjectBars.length" class="dashboard-panel" shadow="never"><template #header><strong>科目平均成绩</strong></template><BarChart title="平均分" :data="subjectBars" /></el-card>
    <el-card v-if="classBars.length" class="dashboard-panel" shadow="never"><template #header><strong>班级平均成绩</strong></template><BarChart title="平均分" :data="classBars" /></el-card>
    <el-card v-if="analysis.exam_trend?.length" class="dashboard-panel" shadow="never"><template #header><strong>考试趋势</strong></template><LineChart title="平均分" :data="analysis.exam_trend" /></el-card>
  </div>
  <el-card v-if="analysis.student_score?.length" class="dashboard-panel" shadow="never"><template #header><strong>学生成绩汇总</strong></template><el-table :data="analysis.student_score"><el-table-column prop="student_id" label="学生编号" /><el-table-column prop="student_name" label="姓名" /><el-table-column prop="score_count" label="有效成绩数" /><el-table-column prop="average" label="平均分" /><el-table-column prop="maximum" label="最高分" /><el-table-column prop="minimum" label="最低分" /></el-table></el-card>
</template>
