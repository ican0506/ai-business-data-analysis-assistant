<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { createManufacturingReport, getManufacturingReport, listManufacturingReports } from '../api/manufacturing'
import ErrorState from '../components/common/ErrorState.vue'
import Loading from '../components/common/Loading.vue'
import EnergyReportSection from '../components/manufacturing/reports/EnergyReportSection.vue'
import EquipmentReportSection from '../components/manufacturing/reports/EquipmentReportSection.vue'
import ExportButtons from '../components/manufacturing/reports/ExportButtons.vue'
import ProductionReportSection from '../components/manufacturing/reports/ProductionReportSection.vue'
import ReportGenerateCard from '../components/manufacturing/reports/ReportGenerateCard.vue'
import ReportSummary from '../components/manufacturing/reports/ReportSummary.vue'

const reports = ref([])
const selectedReport = ref(null)
const loading = ref(false)
const generating = ref(false)
const error = ref('')

async function selectReport(reportId) {
  if (!reportId) return
  selectedReport.value = await getManufacturingReport(reportId)
}

async function loadReports() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    const data = await listManufacturingReports()
    reports.value = data.items || []
    if (reports.value.length) await selectReport(reports.value[0].id)
    else selectedReport.value = null
  } catch (requestError) {
    error.value = requestError.message || '经营报告历史加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

async function generateReport() {
  if (generating.value) return
  generating.value = true
  error.value = ''
  try {
    const report = await createManufacturingReport({})
    reports.value = [report, ...reports.value.filter((item) => item.id !== report.id)]
    selectedReport.value = report
    ElMessage.success('制造业经营报告已生成')
  } catch (requestError) {
    error.value = requestError.message || '经营报告生成失败，请稍后重试。'
  } finally {
    generating.value = false
  }
}

onMounted(() => { void loadReports() })
</script>

<template>
  <section class="manufacturing-reports-view">
    <header class="reports-header"><div><p class="view-eyebrow">EXECUTIVE INSIGHT CENTER</p><h2>制造业经营报告中心</h2><p>报告以生成时保存的快照为准，保证历史结论可追溯。</p></div></header>
    <ReportGenerateCard :loading="generating" @generate="generateReport" />
    <Loading v-if="loading && !reports.length" text="正在加载经营报告历史…" />
    <ErrorState v-if="error" title="经营报告操作失败" :description="error" @retry="loadReports" />
    <template v-else>
      <div class="report-workspace"><el-card shadow="never" class="history-card"><template #header><strong>报告历史</strong></template><el-empty v-if="!reports.length && !loading" description="暂无经营报告，可先生成第一份报告。" :image-size="78" /><div v-else class="history-list"><button v-for="item in reports" :key="item.id" class="history-item" :class="{ active: selectedReport?.id === item.id }" @click="selectReport(item.id)"><strong>{{ item.title }}</strong><span>{{ item.generated_at?.replace('T', ' ') }}</span><el-tag size="small" :type="item.risk_level === '高风险' ? 'danger' : item.risk_level === '中风险' ? 'warning' : 'success'">{{ item.risk_level }}</el-tag></button></div></el-card>
        <div v-if="selectedReport" class="report-detail"><div class="detail-topline"><span>报告 #{{ selectedReport.id }} · {{ selectedReport.ai_mode === 'deepseek' ? 'DeepSeek 深度解释' : '规则引擎总结' }}</span><ExportButtons :report-id="selectedReport.id" /></div><ReportSummary :report="selectedReport" /><ProductionReportSection :analysis="selectedReport.snapshot?.production_analysis" /><EquipmentReportSection :analysis="selectedReport.snapshot?.equipment_analysis" :diagnoses="selectedReport.snapshot?.equipment_diagnoses" /><EnergyReportSection :analysis="selectedReport.snapshot?.energy_analysis" /></div>
        <el-empty v-else class="detail-empty" description="从左侧选择一份经营报告查看快照详情。" :image-size="96" />
      </div>
    </template>
  </section>
</template>

<style scoped>
.reports-header { margin-bottom: 20px; }.reports-header h2 { margin: 6px 0 10px; color: #132d4e; font-size: 30px; }.reports-header p:not(.view-eyebrow) { margin: 0; color: #6b7f99; }.report-workspace { display: grid; grid-template-columns: 290px minmax(0, 1fr); gap: 18px; margin-top: 18px; align-items: start; }.history-card { position: sticky; top: 16px; }.history-list { display: grid; gap: 8px; }.history-item { width: 100%; display: grid; gap: 6px; padding: 12px; border: 1px solid #e2eaf3; background: #fff; border-radius: 8px; text-align: left; cursor: pointer; }.history-item.active { border-color: #2f74e8; background: #eff6ff; }.history-item strong { color: #173658; }.history-item span { color: #72859a; font-size: 12px; }.report-detail { display: grid; gap: 18px; }.detail-topline { display: flex; justify-content: space-between; align-items: center; gap: 12px; color: #6b7f99; font-size: 13px; }.detail-empty { min-height: 360px; }.view-eyebrow { margin: 0; color: #2f74e8; font-weight: 700; font-size: 12px; letter-spacing: .1em; } @media (max-width: 960px) { .report-workspace { grid-template-columns: 1fr; }.history-card { position: static; }.detail-topline { flex-direction: column; align-items: flex-start; } }
</style>
