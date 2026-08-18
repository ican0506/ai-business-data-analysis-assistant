import { describe, expect, it } from 'vitest'

import { CANONICAL_FIELD_GROUPS, formatNumber, resolveDomainDisplay, showMetricValue } from './domainDisplay'

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

  it('不将 NaN 和无限数值渲染为业务指标', () => {
    expect(formatNumber(0)).toBe('0')
    expect(formatNumber(Number.NaN)).toBe('—')
    expect(formatNumber(Number.POSITIVE_INFINITY)).toBe('—')
    expect(showMetricValue(Number.NEGATIVE_INFINITY)).toBe('—')
  })

  it('订单字段映射分组包含真实电商订单的新增规范字段', () => {
    const orderFields = CANONICAL_FIELD_GROUPS.find((group) => group.label === '订单').fields
    expect(orderFields).toEqual(expect.arrayContaining([
      'customer_name', 'category', 'discount', 'payment_method', 'gender', 'age',
    ]))
  })
})
