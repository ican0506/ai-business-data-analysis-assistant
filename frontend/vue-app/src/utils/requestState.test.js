import { beforeEach, describe, expect, it } from 'vitest'
import { beginRequest, endRequest, isRequesting, resetRequests } from './requestState'

describe('requestState', () => {
  beforeEach(resetRequests)
  it('跟踪并发请求，直到最后一个请求结束才关闭全局加载', () => {
    beginRequest(); beginRequest()
    expect(isRequesting.value).toBe(true)
    endRequest(); expect(isRequesting.value).toBe(true)
    endRequest(); expect(isRequesting.value).toBe(false)
  })
})
