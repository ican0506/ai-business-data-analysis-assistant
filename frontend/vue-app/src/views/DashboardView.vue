<script setup>
import DataDistributionChart from '../components/dashboard/DataDistributionChart.vue'
import KpiCard from '../components/dashboard/KpiCard.vue'
import MetricChart from '../components/dashboard/MetricChart.vue'
import RecentAnalysisTable from '../components/dashboard/RecentAnalysisTable.vue'
import TrendChart from '../components/dashboard/TrendChart.vue'
import { dashboardMockData } from '../mock/dashboard'
</script>

<template>
  <section class="dashboard-view">
    <header class="dashboard-intro">
      <div><p class="view-eyebrow">EXECUTIVE OVERVIEW</p><h2>数据驾驶舱</h2><p>实时掌握企业数据资产、分析活动与经营指标表现。</p></div>
      <el-tag type="info" effect="plain">演示数据</el-tag>
    </header>

    <div class="kpi-grid"><KpiCard v-for="item in dashboardMockData.kpis" :key="item.label" :item="item" /></div>

    <div class="dashboard-grid">
      <el-card class="dashboard-panel trend-panel" shadow="never"><template #header><div class="panel-title"><div><strong>数据趋势</strong><span>近 7 日分析任务变化</span></div><el-tag size="small">分析次数</el-tag></div></template><TrendChart :data="dashboardMockData.trend" /></el-card>
      <el-card class="dashboard-panel" shadow="never"><template #header><div class="panel-title"><div><strong>指标完成率</strong><span>各区域目标达成表现</span></div><el-tag size="small" type="success">%</el-tag></div></template><MetricChart :data="dashboardMockData.metrics" /></el-card>
      <el-card class="dashboard-panel" shadow="never"><template #header><div class="panel-title"><div><strong>数据分布</strong><span>已接入数据集类型占比</span></div></div></template><DataDistributionChart :data="dashboardMockData.distribution" /></el-card>
    </div>

    <el-card class="dashboard-panel recent-panel" shadow="never"><template #header><div class="panel-title"><div><strong>最近分析记录</strong><span>最新上传数据的分析执行状态</span></div><el-tag size="small" type="info">Mock</el-tag></div></template><RecentAnalysisTable :rows="dashboardMockData.recentAnalyses" /></el-card>
  </section>
</template>
