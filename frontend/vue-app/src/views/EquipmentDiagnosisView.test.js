import { createApp, nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const route = { params: { name: '水泥磨' } }

vi.mock('vue-router', () => ({ useRoute: () => route }))
vi.mock('../api/equipment', () => ({ diagnoseEquipment: vi.fn() }))
vi.mock('../components/equipment/EquipmentDiagnosisCard.vue', () => ({
  default: { props: ['equipmentName', 'loading'], emits: ['diagnose'], template: '<button :disabled="loading" @click="$emit(\'diagnose\')">重新诊断 {{ equipmentName }}</button>' },
}))
vi.mock('../components/equipment/DiagnosisResult.vue', () => ({
  default: { props: ['diagnosis'], template: '<div>诊断结果 {{ diagnosis.risk_level }} {{ diagnosis.problem_analysis }}</div>' },
}))

import { diagnoseEquipment } from '../api/equipment'
import EquipmentDiagnosisView from './EquipmentDiagnosisView.vue'

async function flush() {
  await Promise.resolve(); await nextTick(); await Promise.resolve(); await nextTick()
}

function mountView() {
  const host = document.createElement('div')
  document.body.appendChild(host)
  createApp(EquipmentDiagnosisView).mount(host)
  return host
}

describe('AI 设备诊断页面', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    diagnoseEquipment.mockResolvedValue({
      equipment_name: '水泥磨',
      risk_level: '高风险',
      problem_analysis: '设备温度异常升高，结合振动数据判断可能存在机械磨损风险。',
      possible_causes: ['轴承磨损'],
      suggestions: ['检查润滑系统'],
    })
  })
  afterEach(() => document.body.replaceChildren())

  it('加载设备名称并自动展示后端诊断结果', async () => {
    const host = mountView()
    await flush()
    expect(diagnoseEquipment).toHaveBeenCalledWith('水泥磨')
    expect(host.textContent).toContain('高风险')
    expect(host.textContent).toContain('设备温度异常升高')
  })

  it('点击重新诊断会再次调用真实诊断接口', async () => {
    const host = mountView()
    await flush()
    host.querySelector('button').click()
    await flush()
    expect(diagnoseEquipment).toHaveBeenCalledTimes(2)
  })
})
