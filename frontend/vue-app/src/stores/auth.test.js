import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('../api/auth', () => ({
  loginRequest: vi.fn(),
  getCurrentUser: vi.fn(),
}))

import { getCurrentUser, loginRequest } from '../api/auth'
import { useAnalysisStore } from './analysis'
import { TOKEN_STORAGE_KEY, useAuthStore } from './auth'

describe('认证状态', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('登录成功后保存 JWT 和用户信息', async () => {
    loginRequest.mockResolvedValue({ access_token: 'demo-jwt-token', token_type: 'bearer' })
    getCurrentUser.mockResolvedValue({ username: 'student_demo', role: 'USER' })

    const auth = useAuthStore()
    await auth.login({ username: 'student_demo', password: 'DemoPass123' })

    expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBe('demo-jwt-token')
    expect(auth.user).toEqual({ username: 'student_demo', role: 'USER' })
    expect(auth.isAuthenticated).toBe(true)
  })

  it('/me 查询失败时回滚 Token，避免半登录状态', async () => {
    loginRequest.mockResolvedValue({ access_token: 'demo-jwt-token', token_type: 'bearer' })
    getCurrentUser.mockRejectedValue(new Error('用户信息读取失败'))

    const auth = useAuthStore()

    await expect(auth.login({ username: 'student_demo', password: 'DemoPass123' })).rejects.toThrow('用户信息读取失败')

    expect(auth.token).toBe('')
    expect(auth.user).toBeNull()
    expect(localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull()
  })

  it('登出时清除当前用户的运行时分析状态', () => {
    const auth = useAuthStore()
    const analysis = useAnalysisStore()
    auth.token = 'demo-jwt-token'
    auth.user = { id: 1, username: 'user_a' }
    analysis.datasetId = 11
    analysis.metrics = { selected_module: { id: 'order' } }
    analysis.fieldMapping = { overrides: { 总评: 'score' } }
    analysis.mappingDialogVisible = true

    auth.logout()

    expect(auth.user).toBeNull()
    expect(analysis.datasetId).toBeNull()
    expect(analysis.metrics).toBeNull()
    expect(analysis.fieldMapping).toBeNull()
    expect(analysis.mappingDialogVisible).toBe(false)
  })
})
