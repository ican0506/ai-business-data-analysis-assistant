import { createApp, nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import PredictionExplanationCard from './PredictionExplanationCard.vue'

const ContainerStub = { template: '<section><slot /><slot name="header" /></section>' }

async function mountCard(explanation) {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const app = createApp(PredictionExplanationCard, { explanation })
  app.component('el-card', ContainerStub)
  app.component('el-tag', ContainerStub)
  app.component('el-empty', { props: ['description'], template: '<div>{{ description }}</div>' })
  app.mount(host)
  await nextTick()
  return host
}

afterEach(() => document.body.replaceChildren())

describe('PredictionExplanationCard', () => {
  it('展示 AI 总结、风险解释和建议列表', async () => {
    const host = await mountCard({
      summary: '设备存在温度和振动持续升高趋势。',
      risk_explanation: '高风险等级由 Python 确定性预测结果决定。',
      suggestions: ['检查润滑系统', '安排设备巡检'],
      mode: 'deepseek',
    })

    expect(host.textContent).toContain('设备存在温度和振动持续升高趋势。')
    expect(host.textContent).toContain('高风险等级由 Python 确定性预测结果决定。')
    expect(host.textContent).toContain('检查润滑系统')
    expect(host.textContent).toContain('安排设备巡检')
  })

  it('展示 DeepSeek 解释模式', async () => {
    const host = await mountCard({ summary: '已生成解释。', risk_explanation: '说明。', suggestions: [], mode: 'deepseek' })

    expect(host.textContent).toContain('DeepSeek 解释')
  })

  it('展示规则降级解释模式', async () => {
    const host = await mountCard({ summary: '已生成规则说明。', risk_explanation: '说明。', suggestions: [], mode: 'rule_based' })

    expect(host.textContent).toContain('规则降级')
  })

  it('解释不存在时展示空状态且不渲染未定义内容', async () => {
    const host = await mountCard(null)

    expect(host.textContent).toContain('暂无 AI 预测解释')
    expect(host.textContent).not.toContain('undefined')
  })
})
