import { beforeEach, describe, expect, it } from 'vitest'

import { addDatasetRecord, loadDatasetHistory, updateDatasetRecord } from './datasetHistory'

describe('数据集前端展示记录', () => {
  beforeEach(() => localStorage.clear())

  it('仅保存成功上传后的记录，并可更新清洗状态', () => {
    addDatasetRecord({ id: 101, fileName: 'sales.xlsx', fileSize: 2048, status: 'UPLOADED', uploadedAt: '2026-08-02 12:00' })
    updateDatasetRecord(101, { status: 'CLEANED', cleaning: { cleanedRowCount: 18 } })

    expect(loadDatasetHistory()).toEqual([expect.objectContaining({ id: 101, status: 'CLEANED', fileName: 'sales.xlsx' })])
  })
})
