import { defineStore } from 'pinia'

import { getCurrentUser, loginRequest } from '../api/auth'

export const TOKEN_STORAGE_KEY = 'ai_insight_token'
const USER_STORAGE_KEY = 'ai_insight_user'

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_STORAGE_KEY) || 'null')
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_STORAGE_KEY) || '',
    user: readStoredUser(),
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },
  actions: {
    async login(credentials) {
      const session = await loginRequest(credentials)
      const token = session.access_token
      this.token = token
      localStorage.setItem(TOKEN_STORAGE_KEY, token)

      try {
        const user = await getCurrentUser()
        this.user = user
        localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user))
      } catch (error) {
        // 登录链路必须原子完成：用户信息读取失败时撤销已写入的会话。
        this.logout()
        throw error
      }
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem(TOKEN_STORAGE_KEY)
      localStorage.removeItem(USER_STORAGE_KEY)
    },
  },
})
