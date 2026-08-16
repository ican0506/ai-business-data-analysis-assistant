import { describe, expect, it } from 'vitest'

import { resolveDomainDisplay, showMetricValue } from './domainDisplay'

describe('动态领域展示', () => {
  it('根据 selected_module 安全解析四种领域，未知领域回退通用展示', () => {
    expect(resolveDomainDisplay({ id: 'order', name: '订单分析' }).id).toBe('order')
    expect(resolveDomainDisplay({ id: 'student_score' }).name).toBe('学生成绩分析')
    expect(resolveDomainDisplay({ id: 'inventory' }).name).toBe('库存分析')
    expect(resolveDomainDisplay({ id: 'unknown' }).id).toBe('generic')
  })

  it('保留真实 0，并将 null 与 undefined 显示为横杠', () => {
    expect(showMetricValue(0)).toBe('0')
    expect(showMetricValue(null)).toBe('—')
    expect(showMetricValue(undefined)).toBe('—')
  })
})
