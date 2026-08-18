<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { cleanDataset, getDatasets } from '../api/datasets'
import CleaningRecord from '../components/datasets/CleaningRecord.vue'
import DatasetDetail from '../components/datasets/DatasetDetail.vue'
import DatasetHistoryList from '../components/datasets/DatasetHistoryList.vue'
import DatasetUpload from '../components/datasets/DatasetUpload.vue'
import FieldMappingDialog from '../components/analysis/FieldMappingDialog.vue'
import { useAnalysisStore } from '../stores/analysis'
import { useAuthStore } from '../stores/auth'
import { setActiveDatasetId, toDatasetRecord } from '../utils/datasetHistory'

const records = ref([])
const cleaningId = ref(null)
const selectedDataset = ref(null)
const detailVisible = ref(false)
const latestCleaningRecord = ref(null)
const mappingVisible = ref(false)
const analysisStore = useAnalysisStore()
const auth = useAuthStore()
const router = useRouter()
const currentMapping = computed(() => analysisStore.fieldMapping)

async function refreshRecords() { records.value = (await getDatasets()).map(toDatasetRecord) }

async function handleUploaded({ dataset }) {
  await refreshRecords()
  setActiveDatasetId(auth.user?.id, dataset.id)
}

function showDetail(dataset) { selectedDataset.value = dataset; detailVisible.value = true }

async function startCleaning(dataset) {
  try { await ElMessageBox.confirm(`确认开始清洗“${dataset.fileName}”吗？`, '数据清洗确认', { type: 'warning' }) } catch { return }
  cleaningId.value = dataset.id
  try {
    const result = await cleanDataset(dataset.id)
    const cleaning = { fileName: dataset.fileName, cleaningRunId: result.cleaning_run_id, sourceRowCount: result.source_row_count, cleanedRowCount: result.cleaned_row_count, removedEmptyRows: result.removed_empty_rows, removedDuplicateRows: result.removed_duplicate_rows }
    await refreshRecords()
    latestCleaningRecord.value = cleaning
    setActiveDatasetId(auth.user?.id, dataset.id)
    ElMessage.success('数据清洗成功。')
  } catch (error) {
    await refreshRecords()
    ElMessage.error(error.message || '数据清洗失败，请稍后重试。')
  } finally { cleaningId.value = null }
}

function openAnalysis(dataset) { setActiveDatasetId(auth.user?.id, dataset.id); router.push({ name: 'dashboard', query: { datasetId: String(dataset.id) } }) }
async function openMapping(dataset) { setActiveDatasetId(auth.user?.id, dataset.id); await analysisStore.load(dataset.id); mappingVisible.value = true }
async function saveMapping(overrides) { try { await analysisStore.saveOverrides(overrides); ElMessage.success('字段映射已保存，分析结果已刷新。') } catch (error) { ElMessage.error(error.message || '字段映射保存失败。') } }
async function resetMapping() { await saveMapping({}) }
onMounted(() => { void refreshRecords() })
</script>

<template>
  <section class="dataset-management-view">
    <header class="dataset-intro"><div><p class="view-eyebrow">DATA ASSETS</p><h2>数据集管理</h2><p>上传、追踪并清洗企业业务数据；列表以当前登录用户的后端数据为准。</p></div><el-tag type="info" effect="plain">当前用户真实数据集</el-tag></header>
    <DatasetUpload @uploaded="handleUploaded" />
    <DatasetHistoryList :records="records" :cleaning-id="cleaningId" @detail="showDetail" @clean="startCleaning" @analyze="openAnalysis" @mapping="openMapping" />
    <CleaningRecord :record="latestCleaningRecord" />
    <DatasetDetail v-model="detailVisible" :dataset="selectedDataset" />
    <FieldMappingDialog v-model="mappingVisible" :mapping="currentMapping" :saving="analysisStore.savingMapping" @save="saveMapping" @reset="resetMapping" />
  </section>
</template>
