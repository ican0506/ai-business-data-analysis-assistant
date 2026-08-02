<script setup>
import { computed } from 'vue'

const props = defineProps({ report: { type: Object, required: true }, loading: Boolean })
defineEmits(['download'])

const typeLabel = computed(() => ({ excel: 'Excel', word: 'Word', pdf: 'PDF' }[props.report.type] || '文件'))
const iconClass = computed(() => `file-icon ${props.report.type}`)
</script>

<template>
  <el-card class="download-report-card" shadow="never">
    <div :class="iconClass">{{ typeLabel.slice(0, 1) }}</div>
    <div class="report-card-copy"><el-tag size="small" effect="plain">{{ typeLabel }}</el-tag><strong>{{ report.reportName }}</strong><span>{{ report.datasetName }} · {{ report.description }}</span></div>
    <el-button type="primary" plain :loading="loading" @click="$emit('download', report)">下载</el-button>
  </el-card>
</template>
