import { createApp, nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../api/manufacturing', () => ({
  createPrediction: vi.fn(),
  getPredictionDetail: vi.fn(),
  getPredictions: vi.fn(),
}))
vi.mock('element-plus', () => ({ ElMessage: { success: vi.fn() } }))
vi.mock('../components/common/Loading.vue', () => ({ default: { template: '<div>加载中</div>' } }))
vi.mock('../components/common/ErrorState.vue', () => ({ default: { props: ['description'], template: '<div>错误 {{ description }}</div>' } }))
vi.mock('../components/manufacturing/prediction/PredictionSummary.vue', () => ({ default: { props: ['prediction'], template: '<div>预测详情 {{ prediction.id }}</div>' } }))
vi.mock('../components/manufacturing/prediction/EquipmentPredictionCard.vue', () => ({ default: { props: ['prediction'], template: '<div>设备预测 {{ prediction.equipment_name }}</div>' } }))
vi.mock('../components/manufacturing/prediction/EnergyPredictionCard.vue', () => ({ default: { props: ['prediction'], template: '<div>能耗预测 {{ prediction.production_line }}</div>' } }))
vi.mock('../components/manufacturing/prediction/ProductionPredictionCard.vue', () => ({ default: { props: ['prediction'], template: '<div>生产预测 {{ prediction.production_line }}</div>' } }))
vi.mock('../components/manufacturing/prediction/PredictionTrendChart.vue', () => ({ default: { props: ['equipmentPredictions', 'energyPrediction', 'productionPrediction'], template: '<div>趋势图 {{ equipmentPredictions.length }} {{ energyPrediction?.trend }} {{ productionPrediction?.trend }}</div>' } }))
vi.mock('../components/manufacturing/prediction/RiskDistributionChart.vue', () => ({ default: { props: ['distribution'], template: '<div>风险分布 {{ distribution.map(item => item.value).join(",") }}</div>' } }))

import { createPrediction, getPredictionDetail, getPredictions } from '../api/manufacturing'
import ManufacturingPredictionView from './ManufacturingPredictionView.vue'

const ButtonStub = { props: ['disabled', 'loading'], emits: ['click'], template: '<button :disabled="disabled" @click="$emit(\'click\')"><slot /></button>' }
const ContainerStub = { template: '<div><slot /><slot name="header" /></div>' }
const InputStub = { props: ['modelValue'], emits: ['update:modelValue'], template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)">' }

async function flush() {
  await Promise.resolve(); await nextTick(); await Promise.resolve(); await nextTick()
}

function prediction(id = 1, type = 'equipment_risk', riskLevel = '高风险') {
  return {
    id,
    prediction_type: type,
    scope_name: type === 'equipment_risk' ? '水泥磨' : '1号线',
    risk_level: riskLevel,
    generated_at: '2026-08-10T10:00:00',
    prediction_result: {
      equipment_predictions: [{ equipment_name: '水泥磨', risk_level: '高风险' }],
      energy_prediction: { production_line: '1号线', warning_level: '中风险', trend: '上升' },
      production_prediction: { production_line: '1号线', trend: '上升' },
    },
  }
}

function mountView() {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const app = createApp(ManufacturingPredictionView)
  app.component('el-card', ContainerStub)
  app.component('el-empty', ContainerStub)
  app.component('el-tag', ContainerStub)
  app.component('el-button', ButtonStub)
  app.component('el-input', InputStub)
  app.component('el-checkbox-group', ContainerStub)
  app.component('el-checkbox', { props: ['label'], template: '<label><input type="checkbox" :value="label"><slot /></label>' })
  app.component('el-pagination', { template: '<div>分页</div>' })
  app.component('el-select', { props: ['modelValue'], emits: ['update:modelValue'], template: '<select class="risk-filter" :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>' })
  app.component('el-option', { props: ['label', 'value'], template: '<option :value="value">{{ label }}</option>' })
  app.mount(host)
  return host
}

describe('ManufacturingPredictionView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getPredictions.mockResolvedValue({ items: [prediction()], total: 1, page: 1, page_size: 10 })
    getPredictionDetail.mockResolvedValue(prediction())
    createPrediction.mockResolvedValue({ id: 2, total: 1, risk_level: '高风险', prediction_result: prediction(2).prediction_result, items: [prediction(2)] })
  })
  afterEach(() => document.body.replaceChildren())

  it('页面加载后读取预测历史并展示首项详情', async () => {
    const host = mountView()
    await flush()

    expect(getPredictions).toHaveBeenCalledWith({ page: 1, page_size: 10 })
    expect(getPredictionDetail).toHaveBeenCalledWith(1)
    expect(host.textContent).toContain('预测详情 1')
  })

  it('点击生成预测后调用 API 并展示返回的预测结果', async () => {
    const host = mountView()
    await flush()

    const generateButton = [...host.querySelectorAll('button')].find((button) => button.textContent.includes('生成预测'))
    generateButton.click()
    await flush()

    expect(createPrediction).toHaveBeenCalledWith(expect.objectContaining({
      prediction_types: ['equipment_risk', 'energy_consumption', 'production_completion'],
      forecast_horizon_days: 7,
    }))
    expect(host.textContent).toContain('预测详情 2')
  })

  it('点击历史记录时读取并展示对应预测详情', async () => {
    getPredictions.mockResolvedValue({ items: [prediction(1), prediction(2, 'energy_consumption')], total: 2, page: 1, page_size: 10 })
    getPredictionDetail.mockResolvedValue(prediction(2, 'energy_consumption'))
    const host = mountView()
    await flush()

    const detailButton = [...host.querySelectorAll('button')].find((button) => button.textContent.includes('查看详情 #2'))
    detailButton.click()
    await flush()

    expect(getPredictionDetail).toHaveBeenLastCalledWith(2)
    expect(host.textContent).toContain('预测详情 2')
  })

  it('历史请求失败时展示后端错误提示', async () => {
    getPredictions.mockRejectedValue(new Error('预测历史读取失败'))
    const host = mountView()
    await flush()

    expect(host.textContent).toContain('预测历史读取失败')
  })

  it('展示风险统计，并向趋势和风险分布组件传递后端预测结果', async () => {
    getPredictions.mockResolvedValue({
      items: [
        prediction(1, 'equipment_risk', '高风险'),
        prediction(2, 'energy_consumption', '中风险'),
        prediction(3, 'production_completion', '正常'),
        prediction(4, 'equipment_risk', '数据不足'),
      ], total: 4, page: 1, page_size: 10,
    })
    getPredictionDetail.mockResolvedValue(prediction(1))
    const host = mountView()
    await flush()

    expect(host.textContent).toContain('预测数量4')
    expect(host.textContent).toContain('高风险1')
    expect(host.textContent).toContain('中风险1')
    expect(host.textContent).toContain('正常1')
    expect(host.textContent).toContain('数据不足1')
    expect(host.textContent).toContain('趋势图 1 上升 上升')
    expect(host.textContent).toContain('风险分布 1,1,1,1')
  })

  it('按风险等级筛选历史记录', async () => {
    getPredictions.mockResolvedValue({
      items: [prediction(1, 'equipment_risk', '高风险'), prediction(2, 'energy_consumption', '正常')], total: 2, page: 1, page_size: 10,
    })
    const host = mountView()
    await flush()

    const filter = host.querySelector('.risk-filter')
    filter.value = '正常'
    filter.dispatchEvent(new Event('change'))
    await flush()

    expect(host.textContent).toContain('查看详情 #2')
    expect(host.textContent).not.toContain('查看详情 #1')
  })
})
