import { createApp, nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import BusinessSuggestion from './BusinessSuggestion.vue'
import RiskAnalysisPanel from './RiskAnalysisPanel.vue'

const CardStub = { template: '<section><slot name="header" /><slot /></section>' }
const DividerStub = { template: '<div><slot /></div>' }
const IconStub = { template: '<i><slot /></i>' }

async function mount(component, props) {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const app = createApp(component, props)
  app.component('el-card', CardStub)
  app.component('el-divider', DividerStub)
  app.component('el-icon', IconStub)
  app.mount(host)
  await nextTick()
  return host
}

afterEach(() => document.body.replaceChildren())

describe('AI 报告列表字段兼容渲染', () => {
  it('将异常和业务问题的单字符串作为一项渲染，而不是逐字符渲染', async () => {
    const host = await mount(RiskAnalysisPanel, {
      anomalies: '温度偏高；振动上升',
      problems: '需要安排巡检',
    })

    expect(host.querySelectorAll('.report-list-item')).toHaveLength(1)
    expect(host.querySelectorAll('.insight-list li')).toHaveLength(1)
    expect(host.textContent).toContain('温度偏高；振动上升')
    expect(host.textContent).toContain('需要安排巡检')
  })

  it('将建议的单字符串作为一项渲染，空值安全显示为空列表', async () => {
    const stringHost = await mount(BusinessSuggestion, { recommendations: '1. 优化库存；2. 调整促销' })
    expect(stringHost.querySelectorAll('.recommendation-list li')).toHaveLength(1)
    expect(stringHost.textContent).toContain('1. 优化库存；2. 调整促销')

    const emptyHost = await mount(BusinessSuggestion, { recommendations: null })
    expect(emptyHost.querySelectorAll('.recommendation-list li')).toHaveLength(0)
  })
})
