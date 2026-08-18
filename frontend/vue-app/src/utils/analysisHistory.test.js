import { beforeEach, describe, expect, it } from 'vitest'

import { loadAnalysisResult, saveAnalysisResult } from './analysisHistory'

describe('analysisHistory', () => {
  beforeEach(() => localStorage.clear())

  it('按用户和数据集保存并读取最近一次 AI 分析结果', () => {
    const report = { summary: '销售额保持增长', anomalies: [], recommendations: [] }

    saveAnalysisResult(1, 12, report)
    saveAnalysisResult(2, 12, { summary: '另一位用户的分析' })

    expect(loadAnalysisResult(1, 12)).toMatchObject({ datasetId: 12, report })
    expect(loadAnalysisResult(1, 13)).toBeNull()
    expect(loadAnalysisResult(2, 12)).toMatchObject({ report: { summary: '另一位用户的分析' } })
  })

  it('读取损坏的本地数据时返回空结果', () => {
    localStorage.setItem('ai_insight_analysis_history:1', '{bad-json')

    expect(loadAnalysisResult(1, 12)).toBeNull()
  })
})
