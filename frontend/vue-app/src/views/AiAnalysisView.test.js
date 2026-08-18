import { createApp, nextTick, reactive } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia } from 'pinia'

const route = reactive({ query: { datasetId: '7' } })

const replace = vi.fn(async (location) => { route.query = location.query })
vi.mock('vue-router', () => ({ useRoute: () => route, useRouter: () => ({ replace }) }))
vi.mock('element-plus', () => ({ ElMessage: { success: vi.fn(), error: vi.fn() } }))
vi.mock('../api/datasets', () => ({ analyzeDataset: vi.fn(), getDatasets: vi.fn() }))
vi.mock('../components/reports/AnalysisLoading.vue', () => ({ default: { template: '<div>AI 分析加载中</div>' } }))
vi.mock('../components/reports/AiSummaryCard.vue', () => ({ default: { template: '<div>{{ report.summary }}</div>', props: ['report'] } }))
vi.mock('../components/reports/RiskAnalysisPanel.vue', () => ({ default: { template: '<div>风险面板</div>' } }))
vi.mock('../components/reports/BusinessSuggestion.vue', () => ({ default: { template: '<div>建议面板</div>' } }))

import { analyzeDataset, getDatasets } from '../api/datasets'
import AiAnalysisView from './AiAnalysisView.vue'

const ButtonStub = { props: ['disabled', 'loading'], emits: ['click'], template: '<button :disabled="disabled" @click="$emit(\'click\')"><slot /></button>' }
const ContainerStub = { template: '<div><slot /></div>' }
const AlertStub = { props: ['description'], template: '<div>{{ description }}<slot /></div>' }

async function flush() {
  await Promise.resolve()
  await nextTick()
  await Promise.resolve()
  await nextTick()
}

function mountView() {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const app = createApp(AiAnalysisView)
  app.use(createPinia())
  app.component('el-button', ButtonStub)
  app.component('el-card', ContainerStub)
  app.component('el-descriptions', ContainerStub)
  app.component('el-descriptions-item', ContainerStub)
  app.component('el-tag', ContainerStub)
  app.component('el-empty', ContainerStub)
  app.component('el-alert', AlertStub)
  app.mount(host)
  return host
}

describe('AI 分析页面', () => {
  beforeEach(() => {
    localStorage.clear()
    route.query = { datasetId: '7' }
    vi.clearAllMocks()
    localStorage.setItem('ai_insight_user', JSON.stringify({ id: 1, username: 'dataset_owner' }))
    getDatasets.mockResolvedValue([
      { id: 7, original_filename: '订单分析测试数据集.xlsx', status: 'CLEANED', row_count: 20, column_count: 6, created_at: '2026-08-18T10:00:00' },
    ])
  })
  afterEach(() => document.body.replaceChildren())

  it('后端返回 rule_based fallback 时正常展示规则分析报告', async () => {
    analyzeDataset.mockResolvedValue({
      mode: 'rule_based',
      summary: '规则分析摘要',
      anomalies: [],
      business_problems: [],
      recommendations: [],
      report: '规则分析报告',
    })
    const host = mountView()
    await flush()
    host.querySelector('button').click()
    await flush()

    expect(analyzeDataset).toHaveBeenCalledWith(7)
    expect(host.textContent).toContain('规则引擎降级结果')
    expect(host.textContent).toContain('规则分析摘要')
    expect(host.textContent).not.toContain('AI 分析未完成')
  })

  it('AI 请求超时时显示明确错误并保留重新分析入口', async () => {
    analyzeDataset.mockRejectedValue(new Error('AI 分析请求超时，请稍后重试。'))
    const host = mountView()
    await flush()
    host.querySelector('button').click()
    await flush()

    expect(host.textContent).toContain('AI 分析请求超时，请稍后重试。')
    expect(host.textContent).toContain('重新分析')
  })
})
