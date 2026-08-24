import { createApp, nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../api/manufacturing', () => ({
  getProductionRecords: vi.fn(),
  getEquipmentRecords: vi.fn(),
  getEnergyRecords: vi.fn(),
}))

vi.mock('../components/manufacturing/ProductionKpiCard.vue', () => ({
  default: { props: ['item'], template: '<div>{{ item.label }}: {{ item.value }}{{ item.suffix }}</div>' },
}))
vi.mock('../components/manufacturing/ProductionTrendChart.vue', () => ({ default: { template: '<div>生产趋势图</div>' } }))
vi.mock('../components/manufacturing/EquipmentStatusChart.vue', () => ({ default: { template: '<div>设备状态分布图</div>' } }))
vi.mock('../components/manufacturing/EnergyTrendChart.vue', () => ({ default: { template: '<div>能耗趋势图</div>' } }))
vi.mock('../components/common/Loading.vue', () => ({ default: { template: '<div>加载中</div>' } }))
vi.mock('../components/common/ErrorState.vue', () => ({ default: { template: '<div>加载失败</div>' } }))

import { getEnergyRecords, getEquipmentRecords, getProductionRecords } from '../api/manufacturing'
import ManufacturingDashboardView from './ManufacturingDashboardView.vue'

const ContainerStub = { template: '<div><slot /><slot name="header" /></div>' }
const ButtonStub = { props: ['loading', 'disabled'], emits: ['click'], template: '<button :disabled="disabled" @click="$emit(\'click\')"><slot /></button>' }

async function flush() {
  await Promise.resolve()
  await nextTick()
  await Promise.resolve()
  await nextTick()
}

function mountDashboard() {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const app = createApp(ManufacturingDashboardView)
  app.component('el-card', ContainerStub)
  app.component('el-button', ButtonStub)
  app.component('el-empty', ContainerStub)
  app.mount(host)
  return host
}

describe('ManufacturingDashboardView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getProductionRecords.mockResolvedValue({
      items: [
        { date: '2026-08-01', production_line: '1号线', clinker_output: 5000, cement_output: 6500, planned_output: 7000 },
        { date: '2026-08-01', production_line: '2号线', clinker_output: 4800, cement_output: 6000, planned_output: 6500 },
        { date: '2026-08-02', production_line: '1号线', clinker_output: 5200, cement_output: 6700, planned_output: 7000 },
      ],
      total: 3,
    })
    getEquipmentRecords.mockResolvedValue({
      items: [
        { date: '2026-08-02', equipment_name: '水泥磨', status: '运行', running_hours: 22.5 },
        { date: '2026-08-02', equipment_name: '回转窑', status: '运行', running_hours: 24 },
      ],
      total: 2,
    })
    getEnergyRecords.mockResolvedValue({
      items: [
        { date: '2026-08-01', production_line: '1号线', unit_energy_consumption: 98.5 },
        { date: '2026-08-02', production_line: '1号线', unit_energy_consumption: 96.2 },
      ],
      total: 2,
    })
  })

  afterEach(() => document.body.replaceChildren())

  it('读取真实记录接口并基于最新日期聚合四项 KPI', async () => {
    const host = mountDashboard()
    await flush()

    expect(getProductionRecords).toHaveBeenCalledTimes(1)
    expect(getEquipmentRecords).toHaveBeenCalledTimes(1)
    expect(getEnergyRecords).toHaveBeenCalledTimes(1)
    expect(host.textContent).toContain('熟料产量: 5,200')
    expect(host.textContent).toContain('水泥产量: 6,700')
    expect(host.textContent).toContain('生产达成率: 95.7%')
    expect(host.textContent).toContain('设备运行率: 96.9%')
    expect(host.textContent).toContain('单位能耗: 96.2')
    expect(host.textContent).toContain('生产趋势图')
    expect(host.textContent).toContain('设备状态分布图')
    expect(host.textContent).toContain('能耗趋势图')
  })

  it('点击刷新时只重新请求三类真实记录接口', async () => {
    const host = mountDashboard()
    await flush()
    const refreshButton = [...host.querySelectorAll('button')].find((button) => button.textContent.trim() === '刷新数据')

    refreshButton.click()
    await flush()

    expect(getProductionRecords).toHaveBeenCalledTimes(2)
    expect(getEquipmentRecords).toHaveBeenCalledTimes(2)
    expect(getEnergyRecords).toHaveBeenCalledTimes(2)
  })
})
