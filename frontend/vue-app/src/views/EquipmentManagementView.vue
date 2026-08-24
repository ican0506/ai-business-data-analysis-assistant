<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { getEquipmentAnomalies, getEquipmentDetail, getEquipmentHistory, getEquipmentList } from '../api/equipment'
import EquipmentAlertCard from '../components/equipment/EquipmentAlertCard.vue'
import EquipmentDetail from '../components/equipment/EquipmentDetail.vue'
import EquipmentList from '../components/equipment/EquipmentList.vue'
import EquipmentTrendChart from '../components/equipment/EquipmentTrendChart.vue'
import ErrorState from '../components/common/ErrorState.vue'
import Loading from '../components/common/Loading.vue'

const equipment = ref([])
const alerts = ref([])
const selectedName = ref('')
const detail = ref(null)
const history = ref([])
const loading = ref(false)
const detailLoading = ref(false)
const error = ref('')

async function selectEquipment(equipmentName) {
  if (!equipmentName || detailLoading.value) return
  selectedName.value = equipmentName
  detailLoading.value = true
  try {
    const [detailData, historyData] = await Promise.all([getEquipmentDetail(equipmentName), getEquipmentHistory(equipmentName)])
    if (selectedName.value !== equipmentName) return
    detail.value = detailData
    history.value = historyData.items || []
  } catch (requestError) {
    error.value = requestError.message || '设备详情加载失败，请稍后重试。'
  } finally {
    detailLoading.value = false
  }
}

async function loadEquipmentManagement({ notify = false } = {}) {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    const [listData, anomalyData] = await Promise.all([getEquipmentList(), getEquipmentAnomalies()])
    equipment.value = listData.items || []
    alerts.value = anomalyData.items || []
    const active = equipment.value.some((item) => item.equipment_name === selectedName.value)
      ? selectedName.value
      : equipment.value[0]?.equipment_name || ''
    if (active) await selectEquipment(active)
    else { selectedName.value = ''; detail.value = null; history.value = [] }
    if (notify) ElMessage.success('设备管理数据已刷新')
  } catch (requestError) {
    error.value = requestError.message || '设备管理数据加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

onMounted(() => { void loadEquipmentManagement() })
</script>

<template>
  <section class="equipment-management-view">
    <header class="management-header">
      <div><p class="view-eyebrow">EQUIPMENT OPERATIONS</p><h2>设备管理</h2><p>查看设备最新运行状态、历史趋势与基于规则的异常告警。</p></div>
      <el-button type="primary" :loading="loading" :disabled="loading" @click="loadEquipmentManagement({ notify: true })">刷新数据</el-button>
    </header>

    <Loading v-if="loading && !equipment.length" text="正在加载设备运行数据…" />
    <ErrorState v-if="error" title="设备管理数据加载失败" :description="error" @retry="loadEquipmentManagement" />
    <template v-else>
      <el-empty v-if="!loading && !equipment.length" description="暂无设备运行记录，请先通过接口录入设备数据。" :image-size="96" />
      <div v-else class="management-grid">
        <EquipmentList class="equipment-list" :items="equipment" :selected-name="selectedName" :loading="loading" @select="selectEquipment" />
        <div class="detail-column">
          <EquipmentDetail :record="detail" />
          <div v-if="detailLoading" class="detail-loading">正在加载设备详情与趋势…</div>
          <div class="trend-grid">
            <EquipmentTrendChart title="温度趋势" metric="temperature" unit="℃" color="#e67e22" :records="history" />
            <EquipmentTrendChart title="振动趋势" metric="vibration" unit="" color="#8e44ad" :records="history" />
          </div>
        </div>
        <EquipmentAlertCard class="alert-column" :alerts="alerts" />
      </div>
    </template>
  </section>
</template>

<style scoped>
.management-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; margin-bottom: 24px; }.management-header h2 { margin: 6px 0 10px; color: #132d4e; font-size: 30px; }.management-header p:not(.view-eyebrow) { margin: 0; color: #6b7f99; }.management-grid { display: grid; grid-template-columns: minmax(340px, 0.9fr) minmax(520px, 1.5fr); gap: 18px; align-items: start; }.alert-column { grid-column: 1 / -1; }.detail-column { display: grid; gap: 18px; }.trend-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }.detail-loading { color: #6b7f99; font-size: 14px; }@media (max-width: 1080px) { .management-grid { grid-template-columns: 1fr; }.trend-grid { grid-template-columns: 1fr; } }@media (max-width: 760px) { .management-header { flex-direction: column; } }
</style>
