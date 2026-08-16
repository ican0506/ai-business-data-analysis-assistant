<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import DomainBadge from '../components/analysis/DomainBadge.vue'
import FieldMappingDialog from '../components/analysis/FieldMappingDialog.vue'
import GenericDashboard from '../components/domain/GenericDashboard.vue'
import InventoryDashboard from '../components/domain/InventoryDashboard.vue'
import OrderDashboard from '../components/domain/OrderDashboard.vue'
import StudentScoreDashboard from '../components/domain/StudentScoreDashboard.vue'
import ErrorState from '../components/common/ErrorState.vue'
import Loading from '../components/common/Loading.vue'
import { useAnalysisStore } from '../stores/analysis'
import { getActiveDatasetId, loadDatasetHistory, setActiveDatasetId } from '../utils/datasetHistory'

const analysisStore = useAnalysisStore()
const route = useRoute()
const router = useRouter()
const records = ref(loadDatasetHistory())
const routeDatasetId = Number(route.query.datasetId)
const initialDatasetId = Number.isInteger(routeDatasetId) && routeDatasetId > 0
  ? routeDatasetId
  : getActiveDatasetId() || records.value[0]?.id || null
const activeDatasetId = ref(initialDatasetId)
const selectedDatasetId = computed({
  get: () => activeDatasetId.value,
  set: (datasetId) => { void selectDataset(datasetId) },
})
const currentDataset = computed(() => records.value.find((item) => item.id === Number(activeDatasetId.value)) || (activeDatasetId.value ? { id: activeDatasetId.value, fileName: `数据集 #${activeDatasetId.value}`, status: '待加载' } : null))
const dashboardComponent = computed(() => ({ order: OrderDashboard, student_score: StudentScoreDashboard, inventory: InventoryDashboard, generic: GenericDashboard }[analysisStore.domain.id] || GenericDashboard))
const mappingVisible = computed({ get: () => Boolean(analysisStore.mappingDialogVisible), set: (value) => { analysisStore.mappingDialogVisible = value } })
function syncDatasetRecords() { records.value = loadDatasetHistory() }
function normalizeDatasetId(datasetId) {
  const normalizedDatasetId = Number(datasetId)
  return Number.isInteger(normalizedDatasetId) && normalizedDatasetId > 0 ? normalizedDatasetId : null
}
async function selectDataset(datasetId, { syncRoute = true } = {}) {
  const normalizedDatasetId = normalizeDatasetId(datasetId)
  if (!normalizedDatasetId) return
  syncDatasetRecords()
  activeDatasetId.value = normalizedDatasetId
  setActiveDatasetId(normalizedDatasetId)
  if (syncRoute && Number(route.query.datasetId) !== normalizedDatasetId) {
    await router.replace({ query: { ...route.query, datasetId: String(normalizedDatasetId) } })
  }
  try {
    await analysisStore.load(normalizedDatasetId)
  } catch {
    // 错误已写入 store，由页面 ErrorState 展示并提供重试。
  }
}
watch(() => route.query.datasetId, (value) => {
  const datasetId = normalizeDatasetId(value)
  if (datasetId && datasetId !== activeDatasetId.value) void selectDataset(datasetId, { syncRoute: false })
})
if (initialDatasetId) void selectDataset(initialDatasetId, { syncRoute: !routeDatasetId })
async function refresh() {
  if (analysisStore.loading || !activeDatasetId.value) return
  try {
    await analysisStore.load(activeDatasetId.value)
    ElMessage.success('数据已刷新')
  } catch (error) {
    ElMessage.error(error.message || '数据刷新失败。')
  }
}
async function saveMapping(overrides) { try { await analysisStore.saveOverrides(overrides); ElMessage.success('字段映射已保存，当前领域和指标已自动刷新。') } catch (error) { ElMessage.error(error.message || '字段映射保存失败。') } }
async function resetMapping() { await saveMapping({}) }
</script>

<template>
  <section class="dashboard-view">
    <header class="dashboard-intro"><div><p class="view-eyebrow">DATASET ANALYSIS</p><h2>数据分析工作区</h2><p>以当前数据集的真实领域识别与后端指标为准，不将缺失指标展示为 0。</p></div><div class="dashboard-actions"><el-select v-model="selectedDatasetId" :disabled="analysisStore.loading || analysisStore.savingMapping" placeholder="选择数据集" class="dataset-select"><el-option v-for="record in records" :key="record.id" :label="record.fileName" :value="record.id" /></el-select><el-button :loading="analysisStore.loading" :disabled="analysisStore.loading || !activeDatasetId" @click="refresh">刷新</el-button><el-button type="primary" :disabled="analysisStore.loading || analysisStore.savingMapping || !activeDatasetId" @click="mappingVisible = true">字段映射</el-button></div></header>
    <el-empty v-if="!currentDataset" description="暂无数据集，请先上传并清洗 CSV 或 Excel 文件。" :image-size="96" />
    <template v-else>
      <el-card class="dataset-context-card" shadow="never"><el-descriptions :column="3" border><el-descriptions-item label="当前数据集">{{ currentDataset.fileName }}</el-descriptions-item><el-descriptions-item label="清洗状态">{{ currentDataset.status }}</el-descriptions-item><el-descriptions-item label="识别结果"><DomainBadge :selected-module="analysisStore.selectedModule" /></el-descriptions-item></el-descriptions></el-card>
      <Loading v-if="analysisStore.loading" text="正在加载真实分析结果…" />
      <ErrorState v-if="analysisStore.error" title="分析结果加载失败" :description="analysisStore.error" @retry="refresh" />
      <component v-if="analysisStore.metrics && !analysisStore.error" :is="dashboardComponent" :key="`${analysisStore.datasetId}-${analysisStore.metricsVersion}-${analysisStore.selectedModule.id}`" :metrics="analysisStore.metrics" />
      <el-empty v-if="!analysisStore.loading && !analysisStore.error && !analysisStore.metrics" description="尚未获得分析结果，请先完成数据清洗。" />
    </template>
    <FieldMappingDialog v-model="mappingVisible" :mapping="analysisStore.fieldMapping" :saving="analysisStore.savingMapping" @save="saveMapping" @reset="resetMapping" />
  </section>
</template>
