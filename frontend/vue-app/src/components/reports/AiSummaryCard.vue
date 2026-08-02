<script setup>
defineProps({ report: { type: Object, required: true } })
</script>

<template>
  <el-card class="report-panel summary-panel" shadow="never">
    <template #header><div class="report-panel-title"><span>01</span><div><strong>业务摘要</strong><small>核心发现与数据概况</small></div></div></template>
    <p class="summary-text">{{ report.summary }}</p>
    <div class="metric-chips">
      <span>有效记录 <b>{{ report.metrics?.total_rows ?? '--' }}</b> 条</span>
      <span>销售额总计 <b>{{ report.metrics?.sales_amount?.total ?? '--' }}</b></span>
      <span>目标完成率 <b>{{ report.metrics?.completion_rate ?? '--' }}{{ report.metrics?.completion_rate == null ? '' : '%' }}</b></span>
    </div>
  </el-card>
</template>
