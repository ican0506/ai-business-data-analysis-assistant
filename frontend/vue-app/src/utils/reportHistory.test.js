import { beforeEach, describe, expect, it } from 'vitest'

import { loadReportHistory, saveReportRecord } from './reportHistory'

describe('reportHistory', () => {
  beforeEach(() => localStorage.clear())

  it('按用户保存下载成功的报告并按时间倒序读取', () => {
    saveReportRecord(1, { datasetId: 7, datasetName: '销售数据.xlsx', type: 'excel', reportName: '销售数据-分析报告.xlsx' })
    saveReportRecord(1, { datasetId: 7, datasetName: '销售数据.xlsx', type: 'pdf', reportName: '销售数据-分析报告.pdf' })
    saveReportRecord(2, { datasetId: 7, datasetName: '销售数据.xlsx', type: 'word', reportName: '另一用户.docx' })

    expect(loadReportHistory(1)).toHaveLength(2)
    expect(loadReportHistory(1)[0]).toMatchObject({ type: 'pdf', datasetId: 7 })
    expect(loadReportHistory(2)).toHaveLength(1)
  })

  it('本地历史损坏时返回空列表', () => {
    localStorage.setItem('ai_insight_report_history:1', '{broken')

    expect(loadReportHistory(1)).toEqual([])
  })
})
