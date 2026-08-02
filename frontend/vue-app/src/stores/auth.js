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
      this.token = session.access_token
      localStorage.setItem(TOKEN_STORAGE_KEY, session.access_token)

      this.user = await getCurrentUser()
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(this.user))
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem(TOKEN_STORAGE_KEY)
      localStorage.removeItem(USER_STORAGE_KEY)
    },
  },
})
