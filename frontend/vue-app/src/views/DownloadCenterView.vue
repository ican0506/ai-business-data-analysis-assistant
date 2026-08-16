<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { downloadDatasetReport } from '../api/datasets'
import ReportCard from '../components/download/ReportCard.vue'
import { loadDatasetHistory } from '../utils/datasetHistory'
import { loadReportHistory, saveReportRecord } from '../utils/reportHistory'

const records = ref(loadDatasetHistory())
const history = ref(loadReportHistory())
const downloadingKey = ref('')

const cards = computed(() => records.value.flatMap((dataset) => [
  { id: `${dataset.id}-excel`, datasetId: dataset.id, datasetName: dataset.fileName, type: 'excel', reportName: `${dataset.fileName}-分析报告.xlsx`, description: '可编辑指标明细与业务摘要' },
  { id: `${dataset.id}-word`, datasetId: dataset.id, datasetName: dataset.fileName, type: 'word', reportName: `${dataset.fileName}-分析报告.docx`, description: '适合汇报与业务复盘的文档报告' },
  { id: `${dataset.id}-pdf`, datasetId: dataset.id, datasetName: dataset.fileName, type: 'pdf', reportName: `${dataset.fileName}-分析报告.pdf`, description: '适合留档与正式分发的固定版报告' },
]))

function formatDate(value) {
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short', hour12: false }).format(new Date(value))
}

function saveBlob(blob, filename) {
  if (!(blob instanceof Blob) || blob.size === 0) throw new Error('报告文件为空，未创建下载。')
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

async function downloadReport(report) {
  downloadingKey.value = report.id
  try {
    const { blob, filename } = await downloadDatasetReport(report.datasetId, report.type)
    saveBlob(blob, filename || report.reportName)
    history.value = saveReportRecord(report)
    ElMessage.success(`${report.type.toUpperCase()} 报告已开始下载。`)
  } catch (error) {
    ElMessage.error(error.message || '报告下载失败，请稍后重试。')
  } finally {
    downloadingKey.value = ''
  }
}
</script>

<template>
  <section class="download-center-view">
    <header class="download-intro"><div><p class="view-eyebrow">REPORT DELIVERY</p><h2>报告下载中心</h2><p>面向汇报、复盘与留档，一键导出 Excel、Word、PDF 三类真实业务报告。</p></div><el-tag type="info" effect="plain">真实导出接口 + 本机历史</el-tag></header>
    <el-alert title="报告将基于当前数据集实时生成" description="后端暂无报告历史查询接口；下方历史仅记录本浏览器成功发起的下载。" type="info" show-icon :closable="false" />
    <section><div class="section-heading"><div><strong>可下载报告</strong><span>每类报告均由后端根据所选数据集即时生成。</span></div><el-tag>{{ cards.length }} 个文件</el-tag></div><el-empty v-if="!cards.length" description="暂无数据集，请先上传业务文件后再导出报告。" /><div v-else class="report-card-grid"><ReportCard v-for="report in cards" :key="report.id" :report="report" :loading="downloadingKey === report.id" @download="downloadReport" /></div></section>
    <el-card class="report-history-card" shadow="never"><template #header><div class="section-heading"><div><strong>最近生成记录</strong><span>仅保存在当前浏览器，不代表服务端历史。</span></div></div></template><el-empty v-if="!history.length" :image-size="58" description="还没有成功下载的报告。" /><el-table v-else :data="history" class="report-history-table"><el-table-column prop="reportName" label="报告名称" min-width="250" /><el-table-column prop="datasetName" label="所属数据集" min-width="180" /><el-table-column label="报告类型" width="110"><template #default="{ row }"><el-tag size="small" effect="plain">{{ row.type.toUpperCase() }}</el-tag></template></el-table-column><el-table-column label="生成时间" min-width="170"><template #default="{ row }">{{ formatDate(row.generatedAt) }}</template></el-table-column><el-table-column label="状态" width="105"><template #default><el-tag size="small" type="success">成功</el-tag></template></el-table-column></el-table></el-card>
  </section>
</template>
