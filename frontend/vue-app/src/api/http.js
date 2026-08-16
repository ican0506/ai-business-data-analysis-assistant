import axios from 'axios'

import { TOKEN_STORAGE_KEY } from '../stores/auth'
import { beginRequest, endRequest } from '../utils/requestState'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 20000,
})

http.interceptors.request.use((config) => {
  beginRequest()
  const token = localStorage.getItem(TOKEN_STORAGE_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => { endRequest(); return response.config.returnRawResponse ? response : response.data },
  async (error) => {
    endRequest()
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
      localStorage.removeItem('ai_insight_user')
      if (window.location.pathname !== '/login') window.location.assign('/login')
    }
    let responseData = error.response?.data
    if (responseData instanceof Blob) {
      try { responseData = JSON.parse(await responseData.text()) } catch { responseData = null }
    }
    const message = responseData?.detail || responseData?.message || '网络请求失败，请稍后重试'
    window.dispatchEvent(new CustomEvent('app-error', { detail: message }))
    return Promise.reject(new Error(message))
  },
)

export default http
