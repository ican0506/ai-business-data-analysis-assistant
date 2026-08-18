<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { analyzeDataset, getDatasets } from '../api/datasets'
import AnalysisLoading from '../components/reports/AnalysisLoading.vue'
import AiSummaryCard from '../components/reports/AiSummaryCard.vue'
import BusinessSuggestion from '../components/reports/BusinessSuggestion.vue'
import RiskAnalysisPanel from '../components/reports/RiskAnalysisPanel.vue'
import { useAuthStore } from '../stores/auth'
import { getActiveDatasetId, setActiveDatasetId, toDatasetRecord } from '../utils/datasetHistory'
import { loadAnalysisResult, saveAnalysisResult } from '../utils/analysisHistory'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const analyzing = ref(false)
const errorMessage = ref('')
const cachedResult = ref(null)
const records = ref([])

const selectedDataset = computed(() => {
  const queryId = Number(route.query.datasetId) || getActiveDatasetId(auth.user?.id)
  return records.value.find((item) => item.id === queryId) || records.value[0] || null
})
const report = computed(() => cachedResult.value?.report || null)
const analyzedAt = computed(() => cachedResult.value?.analyzedAt ? new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short', hour12: false }).format(new Date(cachedResult.value.analyzedAt)) : null)
const analysisStatus = computed(() => analyzing.value ? '分析中' : report.value ? '分析完成' : errorMessage.value ? '分析失败' : '等待分析')

watch(selectedDataset, (dataset) => {
  errorMessage.value = ''
  cachedResult.value = dataset ? loadAnalysisResult(auth.user?.id, dataset.id) : null
}, { immediate: true })

async function loadDatasets() {
  records.value = (await getDatasets()).map(toDatasetRecord)
  const preferredId = Number(route.query.datasetId) || getActiveDatasetId(auth.user?.id)
  const selected = records.value.find((item) => item.id === preferredId) || records.value[0] || null
  if (selected) {
    setActiveDatasetId(auth.user?.id, selected.id)
    if (Number(route.query.datasetId) !== selected.id) await router.replace({ query: { ...route.query, datasetId: String(selected.id) } })
  }
}
onMounted(() => { void loadDatasets() })

async function runAnalysis() {
  if (!selectedDataset.value) return
  analyzing.value = true
  errorMessage.value = ''
  try {
    const result = await analyzeDataset(selectedDataset.value.id)
    cachedResult.value = saveAnalysisResult(auth.user?.id, selectedDataset.value.id, result)
    ElMessage.success('AI 分析报告已生成。')
  } catch (error) {
    errorMessage.value = error.message || 'AI 分析失败，请检查数据集状态后重试。'
  } finally {
    analyzing.value = false
  }
}
</script>

<template>
  <section class="ai-analysis-view">
    <header class="analysis-intro">
      <div><p class="view-eyebrow">AI INSIGHTS</p><h2>AI 分析报告</h2><p>基于真实数据集生成业务摘要、风险研判与可执行的优化建议。</p></div>
      <el-button type="primary" :loading="analyzing" :disabled="!selectedDataset" @click="runAnalysis">{{ report ? '重新分析' : '开始 AI 分析' }}</el-button>
    </header>

    <el-card class="dataset-context-card" shadow="never">
      <template #header><div class="context-header"><strong>当前数据集</strong><el-tag :type="analysisStatus === '分析完成' ? 'success' : analysisStatus === '分析失败' ? 'danger' : 'info'" effect="light">{{ analysisStatus }}</el-tag></div></template>
      <el-empty v-if="!selectedDataset" :image-size="56" description="暂无可分析的数据集，请先在数据集管理页上传文件。" />
      <el-descriptions v-else :column="4" border>
        <el-descriptions-item label="文件名称">{{ selectedDataset.fileName }} · 数据集 #{{ selectedDataset.id }}</el-descriptions-item>
        <el-descriptions-item label="数据更新时间">{{ selectedDataset.uploadedAt || '--' }}</el-descriptions-item>
        <el-descriptions-item label="数据规模">{{ selectedDataset.rowCount ?? '--' }} 行 / {{ selectedDataset.columnCount ?? '--' }} 列</el-descriptions-item>
        <el-descriptions-item label="分析模式">{{ report?.mode === 'deepseek' ? 'DeepSeek' : report ? '规则分析' : '--' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <AnalysisLoading v-if="analyzing" />
    <el-alert v-else-if="errorMessage" class="analysis-error" title="AI 分析未完成" type="error" :description="errorMessage" show-icon :closable="false"><template #default><el-button type="danger" plain @click="runAnalysis">重新分析</el-button></template></el-alert>
    <template v-else-if="report">
      <div class="analysis-meta"><span>最近分析：{{ analyzedAt }}</span><el-tag effect="plain">{{ report.mode === 'deepseek' ? '大模型生成' : '规则引擎降级结果' }}</el-tag></div>
      <div class="report-grid"><AiSummaryCard :report="report" /><RiskAnalysisPanel :anomalies="report.anomalies" :problems="report.business_problems" /><BusinessSuggestion :recommendations="report.recommendations" /></div>
    </template>
    <el-empty v-else :image-size="92" description="选择数据集后即可发起 AI 分析；结果会保存为本浏览器的最近一次记录。" />
  </section>
</template>
