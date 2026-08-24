<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { getEnergyRecords, getEquipmentRecords, getProductionRecords } from '../api/manufacturing'
import ErrorState from '../components/common/ErrorState.vue'
import Loading from '../components/common/Loading.vue'
import EnergyTrendChart from '../components/manufacturing/EnergyTrendChart.vue'
import EquipmentStatusChart from '../components/manufacturing/EquipmentStatusChart.vue'
import ProductionKpiCard from '../components/manufacturing/ProductionKpiCard.vue'
import ProductionTrendChart from '../components/manufacturing/ProductionTrendChart.vue'

const productionRecords = ref([])
const equipmentRecords = ref([])
const energyRecords = ref([])
const loading = ref(false)
const error = ref('')

function latestDate(records) { return records.reduce((latest, item) => !latest || item.date > latest ? item.date : latest, null) }
function number(value) { const parsed = Number(value); return Number.isFinite(parsed) ? parsed : 0 }
function sum(records, field) { return records.reduce((total, item) => total + number(item[field]), 0) }
function format(value, digits = 0) { return Number(value).toLocaleString('zh-CN', { minimumFractionDigits: digits, maximumFractionDigits: digits }) }

const latestProductionDate = computed(() => latestDate(productionRecords.value))
const latestProductionRecords = computed(() => productionRecords.value.filter((item) => item.date === latestProductionDate.value))
const latestEquipmentDate = computed(() => latestDate(equipmentRecords.value))
const latestEquipmentRecords = computed(() => equipmentRecords.value.filter((item) => item.date === latestEquipmentDate.value))
const latestEnergyDate = computed(() => latestDate(energyRecords.value))
const latestEnergyRecords = computed(() => energyRecords.value.filter((item) => item.date === latestEnergyDate.value))

const kpis = computed(() => {
  const clinkerOutput = sum(latestProductionRecords.value, 'clinker_output')
  const cementOutput = sum(latestProductionRecords.value, 'cement_output')
  const plannedOutput = sum(latestProductionRecords.value, 'planned_output')
  const completionRate = plannedOutput > 0 ? cementOutput / plannedOutput * 100 : null
  const equipmentRate = latestEquipmentRecords.value.length
    ? sum(latestEquipmentRecords.value, 'running_hours') / (latestEquipmentRecords.value.length * 24) * 100 : null
  const unitEnergy = latestEnergyRecords.value.length
    ? sum(latestEnergyRecords.value, 'unit_energy_consumption') / latestEnergyRecords.value.length : null
  return [
    { label: '熟料产量', value: format(clinkerOutput), suffix: '吨', note: latestProductionDate.value ? `${latestProductionDate.value} 最新生产数据` : '暂无生产记录' },
    { label: '水泥产量', value: format(cementOutput), suffix: '吨', note: latestProductionDate.value ? `${latestProductionDate.value} 最新生产数据` : '暂无生产记录' },
    { label: '生产达成率', value: completionRate === null ? '—' : format(completionRate, 1), suffix: completionRate === null ? '' : '%', note: plannedOutput > 0 ? '水泥实际产量 / 计划产量' : '暂无计划产量' },
    { label: '设备运行率', value: equipmentRate === null ? '—' : format(equipmentRate, 1), suffix: equipmentRate === null ? '' : '%', note: latestEquipmentRecords.value.length ? '运行时长 / 可用设备时长' : '暂无设备记录' },
    { label: '单位能耗', value: unitEnergy === null ? '—' : format(unitEnergy, 1), suffix: unitEnergy === null ? '' : 'kWh/t', note: latestEnergyDate.value ? `${latestEnergyDate.value} 平均值` : '暂无能源记录' },
  ]
})

const productionTrend = computed(() => Object.values(productionRecords.value.reduce((groups, item) => {
  const row = groups[item.date] ||= { date: item.date, clinker_output: 0, cement_output: 0 }
  row.clinker_output += number(item.clinker_output)
  row.cement_output += number(item.cement_output)
  return groups
}, {})).sort((left, right) => left.date.localeCompare(right.date)))
const lineComparison = computed(() => latestProductionRecords.value.map((item) => ({ production_line: item.production_line, clinker_output: number(item.clinker_output), cement_output: number(item.cement_output) })).sort((left, right) => left.production_line.localeCompare(right.production_line, 'zh-CN')))
const equipmentStatus = computed(() => Object.values(latestEquipmentRecords.value.reduce((groups, item) => {
  groups[item.status] ||= { name: item.status, value: 0 }
  groups[item.status].value += 1
  return groups
}, {})))
const energyTrend = computed(() => Object.values(energyRecords.value.reduce((groups, item) => {
  const row = groups[item.date] ||= { date: item.date, total: 0, count: 0 }
  row.total += number(item.unit_energy_consumption)
  row.count += 1
  return groups
}, {})).map((item) => ({ date: item.date, unit_energy_consumption: item.count ? item.total / item.count : 0 })).sort((left, right) => left.date.localeCompare(right.date)))

async function loadDashboard({ notify = false } = {}) {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    const [production, equipment, energy] = await Promise.all([getProductionRecords(), getEquipmentRecords(), getEnergyRecords()])
    productionRecords.value = production.items || []
    equipmentRecords.value = equipment.items || []
    energyRecords.value = energy.items || []
    if (notify) ElMessage.success('生产经营数据已刷新')
  } catch (requestError) {
    error.value = requestError.message || '制造业数据加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

onMounted(() => { void loadDashboard() })
</script>

<template>
  <section class="manufacturing-dashboard-view">
    <header class="manufacturing-header">
      <div><p class="view-eyebrow">MANUFACTURING OPERATIONS</p><h2>生产经营驾驶舱</h2><p>基于生产、设备与能源真实记录，快速掌握水泥工厂当日运营表现。</p></div>
      <el-button type="primary" :loading="loading" :disabled="loading" @click="loadDashboard({ notify: true })">刷新数据</el-button>
    </header>

    <Loading v-if="loading && !productionRecords.length && !equipmentRecords.length && !energyRecords.length" text="正在加载制造业运营数据…" />
    <ErrorState v-if="error" title="制造业数据加载失败" :description="error" @retry="loadDashboard" />
    <template v-else>
      <div class="manufacturing-kpi-grid"><ProductionKpiCard v-for="item in kpis" :key="item.label" :item="item" /></div>
      <el-empty v-if="!productionRecords.length && !equipmentRecords.length && !energyRecords.length && !loading" description="暂无制造业记录，请先通过接口录入生产、设备或能源数据。" :image-size="96" />
      <div v-else class="manufacturing-chart-grid"><ProductionTrendChart :trend="productionTrend" :line-comparison="lineComparison" /><EquipmentStatusChart :data="equipmentStatus" /><EnergyTrendChart :data="energyTrend" /></div>
    </template>
  </section>
</template>

<style scoped>
.manufacturing-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; margin-bottom: 24px; }
.manufacturing-header h2 { margin: 6px 0 10px; color: #132d4e; font-size: 30px; }
.manufacturing-header p:not(.view-eyebrow) { margin: 0; color: #6b7f99; }
.manufacturing-kpi-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 16px; margin-bottom: 18px; }
.manufacturing-chart-grid { display: grid; gap: 18px; }
@media (max-width: 1260px) { .manufacturing-kpi-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 760px) { .manufacturing-header { flex-direction: column; }.manufacturing-kpi-grid { grid-template-columns: 1fr; } }
</style>
