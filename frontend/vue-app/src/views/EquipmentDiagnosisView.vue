<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute } from 'vue-router'

import { diagnoseEquipment } from '../api/equipment'
import EquipmentDiagnosisCard from '../components/equipment/EquipmentDiagnosisCard.vue'
import DiagnosisResult from '../components/equipment/DiagnosisResult.vue'
import ErrorState from '../components/common/ErrorState.vue'
import Loading from '../components/common/Loading.vue'

const route = useRoute()
const equipmentName = computed(() => String(route.params.name || ''))
const diagnosis = ref(null)
const loading = ref(false)
const error = ref('')

async function loadDiagnosis({ notify = false } = {}) {
  if (!equipmentName.value || loading.value) return
  loading.value = true
  error.value = ''
  try {
    diagnosis.value = await diagnoseEquipment(equipmentName.value)
    if (notify) ElMessage.success('设备 AI 诊断已更新')
  } catch (requestError) {
    error.value = requestError.message || '设备 AI 诊断失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

onMounted(() => { void loadDiagnosis() })
</script>

<template>
  <section class="equipment-diagnosis-view">
    <header class="diagnosis-header"><div><p class="view-eyebrow">INTELLIGENT MAINTENANCE</p><h2>AI 设备诊断助手</h2><p>将已记录的设备运行数据与异常规则转化为可执行的维护建议。</p></div></header>
    <EquipmentDiagnosisCard :equipment-name="equipmentName" :loading="loading" @diagnose="loadDiagnosis({ notify: true })" />
    <Loading v-if="loading && !diagnosis" text="正在生成设备诊断…" />
    <ErrorState v-else-if="error" title="设备 AI 诊断失败" :description="error" @retry="loadDiagnosis" />
    <DiagnosisResult v-else-if="diagnosis" :diagnosis="diagnosis" />
  </section>
</template>

<style scoped>
.equipment-diagnosis-view { display: grid; gap: 18px; }.diagnosis-header h2 { margin: 6px 0 10px; color: #132d4e; font-size: 30px; }.diagnosis-header p:not(.view-eyebrow) { margin: 0; color: #6b7f99; }.view-eyebrow { margin: 0; color: #397af2; font-size: 12px; font-weight: 700; letter-spacing: 1.4px; }
</style>
