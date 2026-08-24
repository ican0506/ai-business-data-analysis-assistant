<script setup>
defineProps({ report: { type: Object, required: true } })
</script>

<template>
  <el-card class="report-summary" shadow="never">
    <template #header><div class="card-header"><strong>AI 经营总结</strong><el-tag :type="report.risk_level === '高风险' ? 'danger' : report.risk_level === '中风险' ? 'warning' : 'success'">{{ report.risk_level }}</el-tag></div></template>
    <p>{{ report.summary }}</p>
    <div v-if="report.snapshot?.ai_summary?.suggestions?.length"><strong>建议措施</strong><ul><li v-for="item in report.snapshot.ai_summary.suggestions" :key="item">{{ item }}</li></ul></div>
  </el-card>
</template>

<style scoped>.card-header { display: flex; align-items: center; justify-content: space-between; }.report-summary p { line-height: 1.8; color: #31516f; }.report-summary ul { margin: 10px 0 0; padding-left: 20px; color: #486581; line-height: 1.8; }</style>
