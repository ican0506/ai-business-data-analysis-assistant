import { createApp, nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../api/manufacturing', () => ({
  createManufacturingReport: vi.fn(),
  getManufacturingReport: vi.fn(),
  listManufacturingReports: vi.fn(),
}))
vi.mock('element-plus', () => ({ ElMessage: { success: vi.fn() } }))
vi.mock('../components/manufacturing/reports/ReportGenerateCard.vue', () => ({ default: { emits: ['generate'], template: '<button @click="$emit(\'generate\')">生成经营报告</button>' } }))
vi.mock('../components/manufacturing/reports/ReportSummary.vue', () => ({ default: { props: ['report'], template: '<div>AI 总结 {{ report.summary }}</div>' } }))
vi.mock('../components/manufacturing/reports/ProductionReportSection.vue', () => ({ default: { props: ['analysis'], template: '<div>生产分析 {{ analysis.cement_output_total }}</div>' } }))
vi.mock('../components/manufacturing/reports/EquipmentReportSection.vue', () => ({ default: { template: '<div>设备分析</div>' } }))
vi.mock('../components/manufacturing/reports/EnergyReportSection.vue', () => ({ default: { template: '<div>能源分析</div>' } }))
vi.mock('../components/manufacturing/reports/ExportButtons.vue', () => ({ default: { template: '<div>报告导出</div>' } }))
vi.mock('../components/common/Loading.vue', () => ({ default: { template: '<div>加载中</div>' } }))
vi.mock('../components/common/ErrorState.vue', () => ({ default: { template: '<div>加载失败</div>' } }))

import { createManufacturingReport, getManufacturingReport, listManufacturingReports } from '../api/manufacturing'
import ManufacturingReportsView from './ManufacturingReportsView.vue'

const ContainerStub = { template: '<div><slot /><slot name="header" /></div>' }

async function flush() {
  await Promise.resolve(); await nextTick(); await Promise.resolve(); await nextTick()
}

function report(id = 1, title = '生产经营日报') {
  return {
    id, title, summary: '生产总体稳定', risk_level: '正常', ai_mode: 'rule_based', generated_at: '2026-08-07T10:00:00',
    snapshot: { production_analysis: { cement_output_total: 6500 }, equipment_analysis: {}, energy_analysis: {} },
  }
}

describe('ManufacturingReportsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    listManufacturingReports.mockResolvedValue({ items: [report()], total: 1 })
    getManufacturingReport.mockResolvedValue(report())
    createManufacturingReport.mockResolvedValue(report(2, '新生成报告'))
  })
  afterEach(() => document.body.replaceChildren())

  it('读取报告历史、展示选中报告的 snapshot，并能生成新报告', async () => {
    const host = document.createElement('div'); document.body.appendChild(host)
    const app = createApp(ManufacturingReportsView)
    app.component('el-card', ContainerStub); app.component('el-empty', ContainerStub); app.component('el-tag', ContainerStub)
    app.mount(host)
    await flush()

    expect(listManufacturingReports).toHaveBeenCalledOnce()
    expect(getManufacturingReport).toHaveBeenCalledWith(1)
    expect(host.textContent).toContain('AI 总结 生产总体稳定')
    expect(host.textContent).toContain('生产分析 6500')

    host.querySelector('button').click()
    await flush()
    expect(createManufacturingReport).toHaveBeenCalledWith({})
    expect(host.textContent).toContain('新生成报告')
  })
})
