<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { createPrediction, getPredictionDetail, getPredictions } from '../api/manufacturing'
import ErrorState from '../components/common/ErrorState.vue'
import Loading from '../components/common/Loading.vue'
import EnergyPredictionCard from '../components/manufacturing/prediction/EnergyPredictionCard.vue'
import EquipmentPredictionCard from '../components/manufacturing/prediction/EquipmentPredictionCard.vue'
import PredictionSummary from '../components/manufacturing/prediction/PredictionSummary.vue'
import PredictionExplanationCard from '../components/manufacturing/prediction/PredictionExplanationCard.vue'
import ProductionPredictionCard from '../components/manufacturing/prediction/ProductionPredictionCard.vue'
import PredictionTrendChart from '../components/manufacturing/prediction/PredictionTrendChart.vue'
import RiskDistributionChart from '../components/manufacturing/prediction/RiskDistributionChart.vue'

const predictionTypes = ref(['equipment_risk', 'energy_consumption', 'production_completion'])
const equipmentName = ref('')
const productionLine = ref('')
const forecastHorizonDays = ref(7)
const predictions = ref([])
const selectedPrediction = ref(null)
const page = ref(1)
const pageSize = 10
const total = ref(0)
const loading = ref(false)
const generating = ref(false)
const error = ref('')
const riskFilter = ref('all')

const typeLabels = { equipment_risk: '设备故障趋势', energy_consumption: '能耗趋势', production_completion: '生产达成' }

function typeLabel(type) { return typeLabels[type] || type }
function riskTagType(level) { return ({ 高风险: 'danger', 中风险: 'warning', 正常: 'success', 数据不足: 'info' }[level] || 'info') }

const riskStatistics = computed(() => {
  const levels = ['高风险', '中风险', '正常', '数据不足']
  return [{ label: '预测数量', value: predictions.value.length }, ...levels.map((level) => ({ label: level, value: predictions.value.filter((item) => item.risk_level === level).length }))]
})
const riskDistribution = computed(() => riskStatistics.value.slice(1).map((item) => ({ name: item.label, value: item.value })))
const filteredPredictions = computed(() => riskFilter.value === 'all' ? predictions.value : predictions.value.filter((item) => item.risk_level === riskFilter.value))

async function selectPrediction(predictionId) {
  if (!predictionId) return
  selectedPrediction.value = await getPredictionDetail(predictionId)
}

async function loadPredictions(targetPage = page.value) {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    const data = await getPredictions({ page: targetPage, page_size: pageSize })
    page.value = data.page || targetPage
    total.value = data.total || 0
    predictions.value = data.items || []
    if (predictions.value.length) await selectPrediction(predictions.value[0].id)
    else selectedPrediction.value = null
  } catch (requestError) {
    error.value = requestError.message || '预测历史读取失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

async function generatePrediction() {
  if (generating.value || !predictionTypes.value.length) return
  generating.value = true
  error.value = ''
  try {
    const data = await createPrediction({
      prediction_types: predictionTypes.value,
      equipment_name: equipmentName.value || undefined,
      production_line: productionLine.value || undefined,
      forecast_horizon_days: forecastHorizonDays.value,
    })
    const created = data.items?.[0] || {
      id: data.id,
      prediction_result: data.prediction_result,
      risk_level: data.risk_level,
    }
    predictions.value = [created, ...predictions.value.filter((item) => item.id !== created.id)]
    total.value += 1
    selectedPrediction.value = created
    ElMessage.success('制造业预测已生成')
  } catch (requestError) {
    error.value = requestError.message || '预测生成失败，请稍后重试。'
  } finally {
    generating.value = false
  }
}

function changePage(targetPage) { void loadPredictions(targetPage) }

onMounted(() => { void loadPredictions() })
</script>

<template>
  <section class="manufacturing-prediction-view">
    <header class="prediction-header"><div><p class="view-eyebrow">MANUFACTURING FORECAST CENTER</p><h2>制造业预测与预警</h2><p>使用后端确定性预测结果追踪设备风险、能耗趋势与生产达成情况。</p></div></header>

    <el-card shadow="never" class="generate-card"><template #header><strong>生成预测快照</strong></template><div class="generate-form"><div class="field-block"><span>预测类型</span><el-checkbox-group v-model="predictionTypes"><el-checkbox label="equipment_risk">设备故障趋势</el-checkbox><el-checkbox label="energy_consumption">能耗趋势</el-checkbox><el-checkbox label="production_completion">生产达成</el-checkbox></el-checkbox-group></div><el-input v-model="equipmentName" placeholder="设备名称（可选，例如：水泥磨）" clearable /><el-input v-model="productionLine" placeholder="生产线（可选，例如：1号线）" clearable /><el-input v-model.number="forecastHorizonDays" type="number" min="1" max="365" placeholder="预测周期（天）" /><el-button type="primary" :loading="generating" :disabled="generating || !predictionTypes.length" @click="generatePrediction">{{ generating ? '正在生成预测…' : '生成预测' }}</el-button></div></el-card>

    <Loading v-if="loading && !predictions.length" text="正在加载预测历史…" />
    <ErrorState v-if="error" title="预测操作失败" :description="error" @retry="loadPredictions" />
    <template v-else><div class="risk-overview"><el-card v-for="item in riskStatistics" :key="item.label" shadow="never" class="risk-stat"><span>{{ item.label }}</span><strong>{{ item.value }}</strong></el-card><RiskDistributionChart :distribution="riskDistribution" /></div><div class="prediction-workspace"><el-card shadow="never" class="history-card"><template #header><div class="history-header"><strong>预测历史</strong><el-select v-model="riskFilter" class="risk-filter" size="small"><el-option label="全部风险" value="all" /><el-option label="高风险" value="高风险" /><el-option label="中风险" value="中风险" /><el-option label="正常" value="正常" /><el-option label="数据不足" value="数据不足" /></el-select></div></template><el-empty v-if="!predictions.length && !loading" description="暂无预测记录，可先生成第一份预测快照。" :image-size="78" /><el-empty v-else-if="!filteredPredictions.length" description="当前风险等级下暂无预测记录。" :image-size="62" /><div v-else class="history-list"><article v-for="item in filteredPredictions" :key="item.id" class="history-item" :class="{ active: selectedPrediction?.id === item.id }"><div><strong>{{ typeLabel(item.prediction_type) }}</strong><span>{{ item.scope_name || '全厂' }} · {{ item.generated_at?.replace('T', ' ') || '刚刚生成' }}</span></div><el-tag size="small" :type="riskTagType(item.risk_level)">{{ item.risk_level || '—' }}</el-tag><el-button link type="primary" @click="selectPrediction(item.id)">查看详情 #{{ item.id }}</el-button></article></div><el-pagination v-if="total > pageSize" background layout="prev, pager, next" :current-page="page" :page-size="pageSize" :total="total" @current-change="changePage" /></el-card><div v-if="selectedPrediction" class="prediction-detail"><PredictionSummary :prediction="selectedPrediction" /><PredictionTrendChart :equipment-predictions="selectedPrediction.prediction_result?.equipment_predictions || []" :energy-prediction="selectedPrediction.prediction_result?.energy_prediction" :production-prediction="selectedPrediction.prediction_result?.production_prediction" /><PredictionExplanationCard :explanation="selectedPrediction.data_snapshot?.prediction_explanation" /><div class="prediction-grid"><EquipmentPredictionCard :prediction="selectedPrediction.prediction_result?.equipment_predictions || []" /><EnergyPredictionCard :prediction="selectedPrediction.prediction_result?.energy_prediction" /><ProductionPredictionCard :prediction="selectedPrediction.prediction_result?.production_prediction" /></div></div><el-empty v-else class="detail-empty" description="从左侧选择一条预测记录查看详情。" :image-size="96" /></div></template>
  </section>
</template>

<style scoped>
.manufacturing-prediction-view { display: grid; gap: 18px; }.prediction-header h2 { margin: 6px 0 10px; color: #132d4e; font-size: 30px; }.prediction-header p:not(.view-eyebrow) { margin: 0; color: #6b7f99; }.view-eyebrow { margin: 0; color: #397af2; font-size: 12px; font-weight: 700; letter-spacing: 1.4px; }.generate-card { border: 1px solid #dce7f5; }.generate-form { display: grid; grid-template-columns: minmax(240px, 1.5fr) repeat(3, minmax(160px, 1fr)) auto; align-items: end; gap: 12px; }.field-block { display: grid; gap: 8px; color: #314a67; font-size: 13px; font-weight: 600; }.risk-overview { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)) minmax(280px, 1.4fr); gap: 14px; }.risk-stat { display: grid; align-content: center; min-height: 110px; }.risk-stat span { color: #6b7f99; font-size: 13px; }.risk-stat strong { margin-top: 10px; color: #173658; font-size: 30px; }.prediction-workspace { display: grid; grid-template-columns: 310px minmax(0, 1fr); gap: 18px; align-items: start; }.history-card { position: sticky; top: 16px; }.history-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }.risk-filter { width: 116px; }.history-list { display: grid; gap: 8px; }.history-item { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 7px 10px; padding: 12px; border: 1px solid #e2eaf3; border-radius: 8px; }.history-item.active { border-color: #2f74e8; background: #eff6ff; }.history-item strong, .history-item span { display: block; }.history-item strong { color: #173658; }.history-item span { margin-top: 5px; color: #72859a; font-size: 12px; }.history-item :last-child { grid-column: 1 / -1; justify-self: start; }.prediction-detail { display: grid; gap: 18px; }.prediction-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; }.detail-empty { min-height: 320px; } @media (max-width: 1280px) { .risk-overview { grid-template-columns: repeat(2, minmax(0, 1fr)); }.generate-form { grid-template-columns: repeat(2, minmax(0, 1fr)); }.prediction-grid { grid-template-columns: 1fr; } } @media (max-width: 900px) { .prediction-workspace { grid-template-columns: 1fr; }.history-card { position: static; } } @media (max-width: 600px) { .risk-overview, .generate-form { grid-template-columns: 1fr; } }
</style>
