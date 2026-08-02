import { describe, expect, it } from 'vitest'

import { dashboardMockData } from './dashboard'

describe('驾驶舱 mock 数据', () => {
  it('提供四项 KPI、三类图表数据和最近分析记录', () => {
    expect(dashboardMockData.kpis).toHaveLength(4)
    expect(dashboardMockData.trend.labels).not.toHaveLength(0)
    expect(dashboardMockData.metrics.labels).not.toHaveLength(0)
    expect(dashboardMockData.distribution).not.toHaveLength(0)
    expect(dashboardMockData.recentAnalyses).not.toHaveLength(0)
  })
})
