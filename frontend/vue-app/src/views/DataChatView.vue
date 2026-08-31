<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { getDatasets } from '../api/datasets'
import { queryDataChat } from '../api/dataChat'

const datasets = ref([])
const activeDatasetId = ref(null)
const question = ref('')
const messages = ref([])
const loading = ref(false)
const errorMessage = ref('')

const suggestions = [
  '5月份销售总额是多少？',
  '5月份销售数量是多少？',
  '销售额最高的5个商品是什么？',
  '每个月销售额是多少？',
  '哪个地区销售额最高？',
]

const selectedDataset = computed(() => datasets.value.find((item) => item.id === activeDatasetId.value) || null)
const canSend = computed(() => Boolean(activeDatasetId.value && question.value.trim() && !loading.value))

async function loadDatasets() {
  try {
    datasets.value = await getDatasets()
  } catch (error) {
    errorMessage.value = error.message || '数据集加载失败，请稍后重试。'
  }
}

function fillQuestion(value) {
  question.value = value
}

function handleKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    void sendQuestion()
  }
}

async function sendQuestion() {
  if (!activeDatasetId.value) {
    ElMessage.warning('请先选择要查询的数据集。')
    return
  }
  const content = question.value.trim()
  if (!content || loading.value) return

  messages.value.push({ role: 'user', content })
  question.value = ''
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await queryDataChat({ dataset_id: activeDatasetId.value, question: content })
    messages.value.push({ role: 'assistant', content: data.answer, evidence: data })
  } catch (error) {
    errorMessage.value = error.message || '数据问答失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

function displayMetrics(evidence) {
  const metrics = evidence?.result?.metrics || {}
  return Object.entries(metrics).map(([key, value]) => ({ key, value }))
}

function metricLabel(key) {
  return { sales_amount: '销售总额', sales_quantity: '销售数量', order_count: '订单数量', average_order_value: '平均客单价' }[key] || key
}

function formatValue(key, value) {
  if (value && typeof value === 'object' && value.status === 'unavailable') return `无法计算：${value.reason || '字段不可用'}`
  if (value === null || value === undefined) return '--'
  const number = Number(value)
  if (!Number.isFinite(number)) return String(value)
  if (key === 'sales_amount' || key === 'average_order_value') return `¥${number.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  return number.toLocaleString('zh-CN')
}

function formatDateRange(range) {
  return range ? `${range.start} ～ ${range.end}` : '全部可用数据'
}

function interpreterLabel(mode) { return mode === 'llm' ? 'AI 解析' : '规则解析' }
function answerModeLabel(mode) { return mode === 'deepseek' ? 'AI 解释' : '规则回答' }

onMounted(() => { void loadDatasets() })
</script>

<template>
  <section class="data-chat-view">
    <header class="chat-header">
      <div><p class="view-eyebrow">DATA CHAT</p><h2>AI 数据问答</h2><p>使用自然语言查询已清洗订单数据，指标始终由系统确定性计算。</p></div>
    </header>

    <el-card shadow="never" class="dataset-card">
      <label for="chat-dataset">查询数据集</label>
      <el-select id="chat-dataset" v-model="activeDatasetId" placeholder="请选择数据集" clearable>
        <el-option v-for="dataset in datasets" :key="dataset.id" :label="dataset.original_filename || dataset.fileName" :value="dataset.id" />
      </el-select>
      <span v-if="selectedDataset" class="dataset-hint">当前选择：{{ selectedDataset.original_filename || selectedDataset.fileName }}</span>
    </el-card>

    <el-alert v-if="errorMessage" type="error" :title="errorMessage" show-icon :closable="false" class="chat-error" />

    <el-card shadow="never" class="chat-card">
      <div v-if="!messages.length" class="chat-empty">
        <el-empty :image-size="92" description="你可以直接询问当前数据集中的业务指标。" />
        <div class="suggestions"><el-button v-for="item in suggestions" :key="item" plain @click="fillQuestion(item)">{{ item }}</el-button></div>
      </div>
      <div v-else class="message-list">
        <article v-for="(message, index) in messages" :key="index" class="message" :class="message.role">
          <span class="message-role">{{ message.role === 'user' ? '你' : 'AI 数据助手' }}</span>
          <div class="message-content">{{ message.content }}</div>
          <template v-if="message.role === 'assistant'">
            <el-tag size="small" effect="plain" :type="message.evidence.answer_mode === 'deepseek' ? 'success' : 'info'">{{ answerModeLabel(message.evidence.answer_mode) }}</el-tag>
            <el-collapse class="evidence"><el-collapse-item title="查看数据依据">
              <dl>
                <div><dt>数据集</dt><dd>{{ message.evidence.dataset?.original_filename }}</dd></div>
                <div><dt>时间范围</dt><dd>{{ formatDateRange(message.evidence.query_plan?.date_range) }}</dd></div>
                <div><dt>查询指标</dt><dd>{{ (message.evidence.query_plan?.metrics || []).map(metricLabel).join('、') || '--' }}</dd></div>
                <div><dt>分组方式</dt><dd>{{ (message.evidence.query_plan?.group_by || []).join('、') || '未分组' }}</dd></div>
                <div><dt>筛选条件</dt><dd>{{ Object.values(message.evidence.query_plan?.filters || {}).filter(Boolean).join('、') || '无' }}</dd></div>
                <div><dt>问题解析</dt><dd>{{ interpreterLabel(message.evidence.interpreter_mode) }}</dd></div>
                <div><dt>回答生成</dt><dd>{{ answerModeLabel(message.evidence.answer_mode) }}</dd></div>
              </dl>
              <div v-if="displayMetrics(message.evidence).length" class="metric-evidence"><strong>计算结果</strong><span v-for="item in displayMetrics(message.evidence)" :key="item.key">{{ metricLabel(item.key) }}：{{ formatValue(item.key, item.value) }}</span></div>
            </el-collapse-item></el-collapse>
          </template>
        </article>
      </div>
      <div v-if="loading" class="thinking">正在分析数据……</div>
      <div class="composer"><el-input v-model="question" type="textarea" :rows="3" maxlength="1000" show-word-limit placeholder="输入你的数据问题，例如：5月份销售额是多少？" :disabled="loading" @keydown="handleKeydown" /><el-button type="primary" :loading="loading" :disabled="!canSend" @click="sendQuestion">发送</el-button></div>
    </el-card>
  </section>
</template>

<style scoped>
.data-chat-view { max-width: 1120px; margin: 0 auto; }.chat-header { margin-bottom: 20px; }.chat-header h2 { margin: 6px 0 10px; color: #132d4e; font-size: 30px; }.chat-header p:not(.view-eyebrow) { margin: 0; color: #6b7f99; }.view-eyebrow { margin: 0; color: #2f74e8; font-weight: 700; font-size: 12px; letter-spacing: .1em; }.dataset-card { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; }.dataset-card label { color: #173658; font-weight: 700; white-space: nowrap; }.dataset-card :deep(.el-select) { width: min(420px, 100%); }.dataset-hint { color: #71849a; font-size: 13px; }.chat-error { margin-bottom: 16px; }.chat-card { min-height: 560px; }.chat-empty { display: grid; justify-items: center; min-height: 350px; align-content: center; }.suggestions { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; max-width: 720px; }.message-list { display: grid; gap: 16px; min-height: 350px; }.message { display: grid; gap: 7px; max-width: min(78%, 760px); padding: 14px 16px; border-radius: 12px; }.message.user { justify-self: end; background: #2f74e8; color: #fff; }.message.assistant { justify-self: start; background: #f3f7fc; border: 1px solid #e1eaf4; color: #193552; }.message-role { font-size: 12px; font-weight: 700; opacity: .8; }.message-content { line-height: 1.7; white-space: pre-wrap; }.evidence { margin-top: 6px; }.evidence dl { display: grid; gap: 6px; margin: 0; }.evidence dl div { display: grid; grid-template-columns: 84px 1fr; gap: 8px; }.evidence dt { color: #71849a; }.evidence dd { margin: 0; color: #294866; }.metric-evidence { display: grid; gap: 5px; margin-top: 10px; padding-top: 10px; border-top: 1px solid #e4ebf3; }.thinking { padding: 14px 0; color: #2f74e8; font-size: 14px; }.composer { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: end; gap: 12px; padding-top: 18px; border-top: 1px solid #e5edf6; } @media (max-width: 700px) { .dataset-card { align-items: flex-start; flex-direction: column; }.dataset-card :deep(.el-select) { width: 100%; }.message { max-width: 92%; }.composer { grid-template-columns: 1fr; }.composer :deep(.el-button) { width: 100%; } }
</style>
