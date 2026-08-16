import { createApp, nextTick, reactive } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

const route = reactive({ query: { datasetId: '1' } })
const replace = vi.fn(async (location) => {
  route.query = location.query
})

vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => ({ replace }),
}))
vi.mock('element-plus', () => ({ ElMessage: { success: vi.fn(), error: vi.fn() } }))
vi.mock('../api/datasets', () => ({
  getDatasetMetrics: vi.fn(),
  getFieldMapping: vi.fn(),
  replaceFieldMapping: vi.fn(),
}))
vi.mock('../components/analysis/DomainBadge.vue', () => ({ default: { template: '<span>{{ selectedModule.id }}</span>', props: ['selectedModule'] } }))
vi.mock('../components/analysis/FieldMappingDialog.vue', () => ({ default: { template: '<div />' } }))
vi.mock('../components/common/Loading.vue', () => ({ default: { template: '<div>加载中</div>' } }))
vi.mock('../components/common/ErrorState.vue', () => ({ default: { template: '<div>加载失败</div>' } }))
vi.mock('../components/domain/OrderDashboard.vue', () => ({ default: { template: '<div>订单指标 {{ metrics.order_count }}</div>', props: ['metrics'] } }))
vi.mock('../components/domain/StudentScoreDashboard.vue', () => ({ default: { template: '<div>成绩指标</div>', props: ['metrics'] } }))
vi.mock('../components/domain/InventoryDashboard.vue', () => ({ default: { template: '<div>库存指标</div>', props: ['metrics'] } }))
vi.mock('../components/domain/GenericDashboard.vue', () => ({ default: { template: '<div>通用指标</div>', props: ['metrics'] } }))

import { getDatasetMetrics, getFieldMapping } from '../api/datasets'
import { useAnalysisStore } from '../stores/analysis'
import DashboardView from './DashboardView.vue'

const SelectStub = {
  props: ['modelValue'],
  emits: ['update:modelValue'],
  template: '<select data-testid="dataset-select" :value="modelValue" @change="$emit(\'update:modelValue\', Number($event.target.value))"><slot /></select>',
}
const OptionStub = { props: ['label', 'value'], template: '<option :value="value">{{ label }}</option>' }
const ButtonStub = { props: ['disabled', 'loading'], emits: ['click'], template: '<button :disabled="disabled" @click="$emit(\'click\')"><slot /></button>' }
const ContainerStub = { template: '<div><slot /></div>' }

async function flush() {
  await Promise.resolve()
  await nextTick()
  await Promise.resolve()
  await nextTick()
}

function mountDashboard() {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const app = createApp(DashboardView)
  app.use(createPinia())
  app.component('el-select', SelectStub)
  app.component('el-option', OptionStub)
  app.component('el-button', ButtonStub)
  app.component('el-card', ContainerStub)
  app.component('el-descriptions', ContainerStub)
  app.component('el-descriptions-item', ContainerStub)
  app.component('el-empty', ContainerStub)
  app.mount(host)
  return host
}

describe('Dashboard 数据集状态同步', () => {
  beforeEach(() => {
    localStorage.clear()
    route.query = { datasetId: '1' }
    replace.mockClear()
    vi.clearAllMocks()
    setActivePinia(createPinia())
    localStorage.setItem('ai_insight_dataset_history', JSON.stringify([
      { id: 1, fileName: 'pandas_dirty_orders_large.xlsx', status: 'CLEANED' },
      { id: 2, fileName: '订单分析测试数据集.xlsx', status: 'CLEANED' },
    ]))
    getFieldMapping.mockResolvedValue({ overrides: {}, field_mapping: { mappings: [] } })
    getDatasetMetrics
      .mockResolvedValueOnce({ selected_module: { id: 'order' }, order_count: 10, top_regions: [{ name: '华东', value: 10 }] })
      .mockResolvedValueOnce({ selected_module: { id: 'order' }, order_count: 20, top_regions: [{ name: '华北', value: 20 }] })
      .mockResolvedValueOnce({ selected_module: { id: 'order' }, order_count: 30, top_regions: [{ name: '华东', value: 30 }] })
  })

  afterEach(() => document.body.replaceChildren())

  it('A → B → A 时选择器、上下文、路由和 metrics 始终使用同一个数据集', async () => {
    const host = mountDashboard()
    await flush()
    const store = useAnalysisStore()
    const select = host.querySelector('[data-testid="dataset-select"]')

    expect(select.value).toBe('1')
    expect(host.textContent).toContain('pandas_dirty_orders_large.xlsx')
    expect(store.datasetId).toBe(1)
    expect(getDatasetMetrics).toHaveBeenLastCalledWith(1)

    select.value = '2'
    select.dispatchEvent(new Event('change'))
    await flush()

    expect(select.value).toBe('2')
    expect(host.textContent).toContain('订单分析测试数据集.xlsx')
    expect(store.datasetId).toBe(2)
    expect(route.query.datasetId).toBe('2')
    expect(localStorage.getItem('ai_insight_active_dataset_id')).toBe('2')
    expect(getFieldMapping).toHaveBeenLastCalledWith(2)
    expect(getDatasetMetrics).toHaveBeenLastCalledWith(2)
    expect(store.metrics.order_count).toBe(20)

    select.value = '1'
    select.dispatchEvent(new Event('change'))
    await flush()

    expect(host.textContent).toContain('pandas_dirty_orders_large.xlsx')
    expect(store.datasetId).toBe(1)
    expect(route.query.datasetId).toBe('1')
    expect(getDatasetMetrics).toHaveBeenLastCalledWith(1)
    expect(store.metrics.order_count).toBe(30)
  })

  it('路由切换到挂载后新增的数据集时会主动同步 localStorage 历史记录', async () => {
    localStorage.setItem('ai_insight_dataset_history', JSON.stringify([
      { id: 1, fileName: 'pandas_dirty_orders_large.xlsx', status: 'CLEANED' },
    ]))
    const host = mountDashboard()
    await flush()

    localStorage.setItem('ai_insight_dataset_history', JSON.stringify([
      { id: 2, fileName: '订单分析测试数据集.xlsx', status: 'CLEANED' },
      { id: 1, fileName: 'pandas_dirty_orders_large.xlsx', status: 'CLEANED' },
    ]))
    route.query = { datasetId: '2' }
    await flush()

    expect(host.querySelector('[data-testid="dataset-select"]').value).toBe('2')
    expect(host.textContent).toContain('订单分析测试数据集.xlsx')
    expect(useAnalysisStore().datasetId).toBe(2)
  })

  it('单次刷新只触发一轮请求，加载期间禁止重复刷新', async () => {
    const host = mountDashboard()
    await flush()
    getFieldMapping.mockReset()
    getDatasetMetrics.mockReset()

    let resolveMapping
    let resolveMetrics
    getFieldMapping.mockImplementationOnce(() => new Promise((resolve) => { resolveMapping = resolve }))
    getDatasetMetrics.mockImplementationOnce(() => new Promise((resolve) => { resolveMetrics = resolve }))

    const refresh = [...host.querySelectorAll('button')].find((button) => button.textContent.trim() === '刷新')
    refresh.click()
    await nextTick()

    expect(refresh.disabled).toBe(true)
    refresh.click()
    expect(getFieldMapping).toHaveBeenCalledTimes(1)
    expect(getDatasetMetrics).toHaveBeenCalledTimes(1)

    resolveMapping({ overrides: {}, field_mapping: { mappings: [] } })
    resolveMetrics({ selected_module: { id: 'order' }, order_count: 99, top_regions: [{ name: '华南', value: 99 }] })
    await flush()

    expect(useAnalysisStore().metrics.order_count).toBe(99)
    expect(host.textContent).toContain('订单指标 99')
  })
})
