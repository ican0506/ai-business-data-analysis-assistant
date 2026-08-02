import { beforeEach, describe, expect, it } from 'vitest'

import { loadReportHistory, saveReportRecord } from './reportHistory'

describe('reportHistory', () => {
  beforeEach(() => localStorage.clear())

  it('保存下载成功的报告并按时间倒序读取', () => {
    saveReportRecord({ datasetId: 7, datasetName: '销售数据.xlsx', type: 'excel', reportName: '销售数据-分析报告.xlsx' })
    saveReportRecord({ datasetId: 7, datasetName: '销售数据.xlsx', type: 'pdf', reportName: '销售数据-分析报告.pdf' })

    expect(loadReportHistory()).toHaveLength(2)
    expect(loadReportHistory()[0]).toMatchObject({ type: 'pdf', datasetId: 7 })
  })

  it('本地历史损坏时返回空列表', () => {
    localStorage.setItem('ai_insight_report_history', '{broken')

    expect(loadReportHistory()).toEqual([])
  })
})
