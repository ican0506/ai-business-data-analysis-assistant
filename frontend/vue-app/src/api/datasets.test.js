import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('./http', () => ({
  default: { post: vi.fn(), get: vi.fn(), put: vi.fn() },
}))

import http from './http'
import { analyzeDataset, cleanDataset } from './datasets'

describe('数据集 API 请求配置', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    http.post.mockResolvedValue({ data: { mode: 'rule_based' } })
  })

  it('AI 分析使用独立的 60 秒 timeout，不改变全局默认值', async () => {
    await analyzeDataset(12)

    expect(http.post).toHaveBeenCalledWith(
      '/api/v1/datasets/12/ai-analysis',
      null,
      { timeout: 60000, timeoutMessage: 'AI 分析请求超时，请稍后重试。' },
    )
  })

  it('普通清洗请求不设置 AI 专属 timeout', async () => {
    await cleanDataset(12)

    expect(http.post).toHaveBeenCalledWith('/api/v1/datasets/12/clean')
  })
})
