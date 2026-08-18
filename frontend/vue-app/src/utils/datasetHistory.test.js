import { beforeEach, describe, expect, it } from 'vitest'

import { clearActiveDatasetId, datasetLabel, getActiveDatasetId, setActiveDatasetId, toDatasetRecord } from './datasetHistory'

describe('数据集前端展示状态', () => {
  beforeEach(() => localStorage.clear())

  it('按用户隔离当前数据集，且不读取旧的全局历史记录', () => {
    localStorage.setItem('ai_insight_active_dataset_id', '99')
    setActiveDatasetId(1, 101)
    setActiveDatasetId(2, 202)

    expect(getActiveDatasetId(1)).toBe(101)
    expect(getActiveDatasetId(2)).toBe(202)
    expect(getActiveDatasetId(3)).toBeNull()

    clearActiveDatasetId(1)
    expect(getActiveDatasetId(1)).toBeNull()
    expect(getActiveDatasetId(2)).toBe(202)
  })

  it('将后端数据集转换为展示记录，并用 ID 与时间区分同名文件', () => {
    const record = toDatasetRecord({
      id: 101,
      original_filename: 'sales.xlsx',
      status: 'CLEANED',
      row_count: 18,
      column_count: 6,
      created_at: '2026-08-18T10:00:00',
    })

    expect(record).toMatchObject({ id: 101, fileName: 'sales.xlsx', rowCount: 18, columnCount: 6 })
    expect(datasetLabel(record)).toContain('数据集 #101')
  })
})
