import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('../api/datasets', () => ({
  getDatasetMetrics: vi.fn(),
  getFieldMapping: vi.fn(),
  replaceFieldMapping: vi.fn(),
}))

import { getDatasetMetrics, getFieldMapping, replaceFieldMapping } from '../api/datasets'
import { useAnalysisStore } from './analysis'

describe('当前数据集分析状态', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('加载字段映射与指标，并根据后端 selected_module 更新当前领域', async () => {
    getFieldMapping.mockResolvedValue({ overrides: {}, field_mapping: { mappings: [] } })
    getDatasetMetrics.mockResolvedValue({ selected_module: { id: 'inventory', name: '库存分析' }, inventory_analysis: { inventory_count: 2 } })

    const store = useAnalysisStore()
    await store.load(7)

    expect(store.datasetId).toBe(7)
    expect(store.domain.id).toBe('inventory')
    expect(store.metrics.inventory_analysis.inventory_count).toBe(2)
  })

  it('保存全量 override 后重新读取映射和指标', async () => {
    getFieldMapping.mockResolvedValue({ overrides: {}, field_mapping: { mappings: [] } })
    getDatasetMetrics
      .mockResolvedValueOnce({ selected_module: { id: 'generic' } })
      .mockResolvedValueOnce({ selected_module: { id: 'student_score' }, student_score_analysis: { student_count: 3 } })
    replaceFieldMapping.mockResolvedValue({ overrides: { 总评: 'score' }, field_mapping: { mappings: [] } })
    const store = useAnalysisStore()
    await store.load(8)

    await store.saveOverrides({ 总评: 'score' })

    expect(replaceFieldMapping).toHaveBeenCalledWith(8, { 总评: 'score' })
    expect(getFieldMapping).toHaveBeenCalledTimes(2)
    expect(getDatasetMetrics).toHaveBeenCalledTimes(2)
    expect(store.domain.id).toBe('student_score')
    expect(store.metrics.student_score_analysis.student_count).toBe(3)
  })

  it('同一数据集连续刷新后保留最新 metrics 并更新渲染版本', async () => {
    getFieldMapping.mockResolvedValue({ overrides: {}, field_mapping: { mappings: [] } })
    getDatasetMetrics
      .mockResolvedValueOnce({ selected_module: { id: 'order' }, order_count: 2, top_regions: [{ name: '华东', value: 100 }] })
      .mockResolvedValueOnce({ selected_module: { id: 'order' }, order_count: 3, top_regions: [{ name: '华东', value: 180 }] })

    const store = useAnalysisStore()
    await store.load(8)
    const firstVersion = store.metricsVersion
    await store.load(8)

    expect(store.metrics.order_count).toBe(3)
    expect(store.metrics.top_regions).toEqual([{ name: '华东', value: 180 }])
    expect(store.metricsVersion).toBe(firstVersion + 1)
    expect(store.loading).toBe(false)
  })

  it('后发起的数据集加载结果不会被先前请求覆盖', async () => {
    let resolveFirst
    getFieldMapping
      .mockImplementationOnce(() => new Promise((resolve) => { resolveFirst = resolve }))
      .mockResolvedValueOnce({ overrides: {}, field_mapping: { mappings: [] } })
    getDatasetMetrics
      .mockResolvedValueOnce({ selected_module: { id: 'order' } })
      .mockResolvedValueOnce({ selected_module: { id: 'inventory' } })

    const store = useAnalysisStore()
    const firstRequest = store.load(1)
    await store.load(2)
    resolveFirst({ overrides: {}, field_mapping: { mappings: [] } })
    await firstRequest

    expect(store.datasetId).toBe(2)
    expect(store.domain.id).toBe('inventory')
  })
})
