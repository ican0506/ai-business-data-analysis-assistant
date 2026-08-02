<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'
import { ref } from 'vue'

import { cleanDataset } from '../api/datasets'
import CleaningRecord from '../components/datasets/CleaningRecord.vue'
import DatasetDetail from '../components/datasets/DatasetDetail.vue'
import DatasetHistoryList from '../components/datasets/DatasetHistoryList.vue'
import DatasetUpload from '../components/datasets/DatasetUpload.vue'
import { addDatasetRecord, loadDatasetHistory, updateDatasetRecord } from '../utils/datasetHistory'

const records = ref(loadDatasetHistory())
const cleaningId = ref(null)
const selectedDataset = ref(null)
const detailVisible = ref(false)
const latestCleaningRecord = ref(null)

function refreshRecords(nextRecords) { records.value = nextRecords }
function formatDate() { return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short', hour12: false }).format(new Date()).replaceAll('/', '-') }

function handleUploaded({ dataset, file }) {
  refreshRecords(addDatasetRecord({ id: dataset.id, fileName: dataset.original_filename, fileSize: file.size, uploadedAt: formatDate(), status: dataset.status, rowCount: dataset.row_count, columnCount: dataset.column_count, columns: dataset.columns, preview: dataset.preview }))
}

function showDetail(dataset) { selectedDataset.value = dataset; detailVisible.value = true }

async function startCleaning(dataset) {
  try { await ElMessageBox.confirm(`确认开始清洗“${dataset.fileName}”吗？`, '数据清洗确认', { type: 'warning' }) } catch { return }
  cleaningId.value = dataset.id
  refreshRecords(updateDatasetRecord(dataset.id, { status: 'CLEANING' }))
  try {
    const result = await cleanDataset(dataset.id)
    const cleaning = { fileName: dataset.fileName, cleaningRunId: result.cleaning_run_id, sourceRowCount: result.source_row_count, cleanedRowCount: result.cleaned_row_count, removedEmptyRows: result.removed_empty_rows, removedDuplicateRows: result.removed_duplicate_rows }
    refreshRecords(updateDatasetRecord(dataset.id, { status: 'CLEANED', cleaning }))
    latestCleaningRecord.value = cleaning
    ElMessage.success('数据清洗成功。')
  } catch (error) {
    refreshRecords(updateDatasetRecord(dataset.id, { status: 'FAILED' }))
    ElMessage.error(error.message || '数据清洗失败，请稍后重试。')
  } finally { cleaningId.value = null }
}
</script>

<template>
  <section class="dataset-management-view">
    <header class="dataset-intro"><div><p class="view-eyebrow">DATA ASSETS</p><h2>数据集管理</h2><p>上传、追踪并清洗企业业务数据；当前列表为本浏览器的成功上传展示记录。</p></div><el-tag type="info" effect="plain">真实接口 + 本机记录</el-tag></header>
    <DatasetUpload @uploaded="handleUploaded" />
    <DatasetHistoryList :records="records" :cleaning-id="cleaningId" @detail="showDetail" @clean="startCleaning" />
    <CleaningRecord :record="latestCleaningRecord" />
    <DatasetDetail v-model="detailVisible" :dataset="selectedDataset" />
  </section>
</template>
