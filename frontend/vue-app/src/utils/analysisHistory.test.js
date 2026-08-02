import { beforeEach, describe, expect, it } from 'vitest'

import { loadAnalysisResult, saveAnalysisResult } from './analysisHistory'

describe('analysisHistory', () => {
  beforeEach(() => localStorage.clear())

  it('按数据集保存并读取最近一次 AI 分析结果', () => {
    const report = { summary: '销售额保持增长', anomalies: [], recommendations: [] }

    saveAnalysisResult(12, report)

    expect(loadAnalysisResult(12)).toMatchObject({ datasetId: 12, report })
    expect(loadAnalysisResult(13)).toBeNull()
  })

  it('读取损坏的本地数据时返回空结果', () => {
    localStorage.setItem('ai_insight_analysis_history', '{bad-json')

    expect(loadAnalysisResult(12)).toBeNull()
  })
})
