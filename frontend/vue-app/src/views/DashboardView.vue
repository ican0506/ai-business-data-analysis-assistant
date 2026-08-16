<script setup>
import { computed, ref, watch } from 'vue'
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
const records = computed(() => loadDatasetHistory())
const activeDatasetId = ref(getActiveDatasetId() || records.value[0]?.id || null)
const currentDataset = computed(() => records.value.find((item) => item.id === Number(activeDatasetId.value)) || null)
const dashboardComponent = computed(() => ({ order: OrderDashboard, student_score: StudentScoreDashboard, inventory: InventoryDashboard, generic: GenericDashboard }[analysisStore.domain.id] || GenericDashboard))
const mappingVisible = computed({ get: () => Boolean(analysisStore.mappingDialogVisible), set: (value) => { analysisStore.mappingDialogVisible = value } })
watch(activeDatasetId, async (datasetId) => { if (datasetId) { setActiveDatasetId(datasetId); await analysisStore.load(datasetId) } }, { immediate: true })
async function refresh() { if (activeDatasetId.value) await analysisStore.load(activeDatasetId.value) }
async function saveMapping(overrides) { try { await analysisStore.saveOverrides(overrides); ElMessage.success('字段映射已保存，当前领域和指标已自动刷新。') } catch (error) { ElMessage.error(error.message || '字段映射保存失败。') } }
async function resetMapping() { await saveMapping({}) }
</script>

<template>
  <section class="dashboard-view">
    <header class="dashboard-intro"><div><p class="view-eyebrow">DATASET ANALYSIS</p><h2>数据分析工作区</h2><p>以当前数据集的真实领域识别与后端指标为准，不将缺失指标展示为 0。</p></div><div class="dashboard-actions"><el-select v-model="activeDatasetId" placeholder="选择数据集" class="dataset-select"><el-option v-for="record in records" :key="record.id" :label="record.fileName" :value="record.id" /></el-select><el-button :disabled="!activeDatasetId" @click="refresh">刷新</el-button><el-button type="primary" :disabled="!activeDatasetId" @click="mappingVisible = true">字段映射</el-button></div></header>
    <el-empty v-if="!currentDataset" description="暂无数据集，请先上传并清洗 CSV 或 Excel 文件。" :image-size="96" />
    <template v-else>
      <el-card class="dataset-context-card" shadow="never"><el-descriptions :column="3" border><el-descriptions-item label="当前数据集">{{ currentDataset.fileName }}</el-descriptions-item><el-descriptions-item label="清洗状态">{{ currentDataset.status }}</el-descriptions-item><el-descriptions-item label="识别结果"><DomainBadge :selected-module="analysisStore.selectedModule" /></el-descriptions-item></el-descriptions></el-card>
      <Loading v-if="analysisStore.loading" text="正在加载真实分析结果…" />
      <ErrorState v-else-if="analysisStore.error" title="分析结果加载失败" :description="analysisStore.error" @retry="refresh" />
      <component :is="dashboardComponent" v-else-if="analysisStore.metrics" :metrics="analysisStore.metrics" />
      <el-empty v-else description="尚未获得分析结果，请先完成数据清洗。" />
    </template>
    <FieldMappingDialog v-model="mappingVisible" :mapping="analysisStore.fieldMapping" :saving="analysisStore.savingMapping" @save="saveMapping" @reset="resetMapping" />
  </section>
</template>
