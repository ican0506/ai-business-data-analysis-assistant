import { createApp, nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('element-plus', () => ({ ElMessage: { success: vi.fn(), error: vi.fn() } }))
vi.mock('../api/equipment', () => ({
  getEquipmentAnomalies: vi.fn(),
  getEquipmentDetail: vi.fn(),
  getEquipmentHistory: vi.fn(),
  getEquipmentList: vi.fn(),
}))
vi.mock('../components/equipment/EquipmentAlertCard.vue', () => ({ default: { props: ['alerts'], template: '<div>异常告警 {{ alerts.length }}</div>' } }))
vi.mock('../components/equipment/EquipmentDetail.vue', () => ({ default: { props: ['record'], template: '<div>设备详情 {{ record?.equipment_name }}</div>' } }))
vi.mock('../components/equipment/EquipmentList.vue', () => ({ default: { props: ['items', 'selectedName', 'loading'], emits: ['select'], template: '<div><button v-for="item in items" :key="item.equipment_name" @click="$emit(\'select\', item.equipment_name)">{{ item.equipment_name }}</button></div>' } }))
vi.mock('../components/equipment/EquipmentTrendChart.vue', () => ({ default: { props: ['title', 'records'], template: '<div>{{ title }} {{ records.length }}</div>' } }))
vi.mock('../components/common/Loading.vue', () => ({ default: { template: '<div>加载中</div>' } }))
vi.mock('../components/common/ErrorState.vue', () => ({ default: { template: '<div>加载失败</div>' } }))

import { getEquipmentAnomalies, getEquipmentDetail, getEquipmentHistory, getEquipmentList } from '../api/equipment'
import EquipmentManagementView from './EquipmentManagementView.vue'

const ButtonStub = { props: ['disabled', 'loading'], emits: ['click'], template: '<button :disabled="disabled" @click="$emit(\'click\')"><slot /></button>' }
const ContainerStub = { template: '<div><slot /></div>' }

async function flush() {
  await Promise.resolve()
  await nextTick()
  await Promise.resolve()
  await nextTick()
}

function mountView() {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const app = createApp(EquipmentManagementView)
  app.component('el-button', ButtonStub)
  app.component('el-card', ContainerStub)
  app.component('el-empty', ContainerStub)
  app.mount(host)
  return host
}

describe('设备管理页面', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getEquipmentList.mockResolvedValue({ items: [{ equipment_name: '水泥磨', status: '运行', temperature: 83, vibration: 5.4 }], total: 1 })
    getEquipmentAnomalies.mockResolvedValue({ items: [{ equipment_name: '水泥磨', rule_id: 'temperature' }], total: 1 })
    getEquipmentDetail.mockResolvedValue({ equipment_name: '水泥磨', status: '运行', temperature: 83, vibration: 5.4 })
    getEquipmentHistory.mockResolvedValue({ equipment_name: '水泥磨', items: [{ date: '2026-08-01', temperature: 65, vibration: 3.2 }, { date: '2026-08-02', temperature: 83, vibration: 5.4 }], total: 2 })
  })

  afterEach(() => document.body.replaceChildren())

  it('加载真实设备列表、告警，并为首个设备展示详情和两类趋势图', async () => {
    const host = mountView()
    await flush()

    expect(getEquipmentList).toHaveBeenCalledOnce()
    expect(getEquipmentAnomalies).toHaveBeenCalledOnce()
    expect(getEquipmentDetail).toHaveBeenCalledWith('水泥磨')
    expect(getEquipmentHistory).toHaveBeenCalledWith('水泥磨')
    expect(host.textContent).toContain('设备详情 水泥磨')
    expect(host.textContent).toContain('温度趋势 2')
    expect(host.textContent).toContain('振动趋势 2')
    expect(host.textContent).toContain('异常告警 1')
  })
})
