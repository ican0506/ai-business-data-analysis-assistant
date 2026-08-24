<script setup>
defineProps({ analysis: { type: Object, default: () => ({}) } })
</script>

<template>
  <el-card shadow="never"><template #header><strong>生产分析</strong></template>
    <el-descriptions :column="4" border><el-descriptions-item label="熟料总产量">{{ analysis.clinker_output_total ?? '--' }}</el-descriptions-item><el-descriptions-item label="水泥总产量">{{ analysis.cement_output_total ?? '--' }}</el-descriptions-item><el-descriptions-item label="计划总产量">{{ analysis.planned_output_total ?? '--' }}</el-descriptions-item><el-descriptions-item label="完成率">{{ analysis.completion_rate ?? '--' }}<template v-if="analysis.completion_rate !== null && analysis.completion_rate !== undefined">%</template></el-descriptions-item></el-descriptions>
    <el-table v-if="analysis.production_line_comparison?.length" :data="analysis.production_line_comparison" class="section-table"><el-table-column prop="production_line" label="生产线" /><el-table-column prop="clinker_output" label="熟料产量" /><el-table-column prop="cement_output" label="水泥产量" /><el-table-column prop="planned_output" label="计划产量" /><el-table-column prop="completion_rate" label="完成率" /></el-table>
  </el-card>
</template>

<style scoped>.section-table { width: 100%; margin-top: 16px; }</style>
