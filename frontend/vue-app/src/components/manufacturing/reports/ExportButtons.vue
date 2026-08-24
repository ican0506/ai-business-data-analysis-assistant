<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

import { downloadManufacturingReport } from '../../../api/manufacturing'

const props = defineProps({ reportId: { type: Number, required: true } })
const downloading = ref('')

async function download(reportFormat) {
  if (downloading.value) return
  downloading.value = reportFormat
  try {
    const response = await downloadManufacturingReport(props.reportId, reportFormat)
    const url = URL.createObjectURL(response.data)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `manufacturing-report-${props.reportId}.${reportFormat === 'excel' ? 'xlsx' : reportFormat === 'word' ? 'docx' : 'pdf'}`
    anchor.click()
    URL.revokeObjectURL(url)
    ElMessage.success('报告下载已开始')
  } finally {
    downloading.value = ''
  }
}
</script>

<template><el-card shadow="never" class="export-buttons"><strong>报告导出</strong><div><el-button v-for="item in [{ id: 'excel', name: 'Excel' }, { id: 'word', name: 'Word' }, { id: 'pdf', name: 'PDF' }]" :key="item.id" plain type="primary" :loading="downloading === item.id" :disabled="Boolean(downloading)" @click="download(item.id)">导出 {{ item.name }}</el-button></div></el-card></template>

<style scoped>.export-buttons :deep(.el-card__body) { display: flex; justify-content: space-between; align-items: center; gap: 14px; }.export-buttons div { display: flex; flex-wrap: wrap; gap: 8px; }</style>
