import http from './http'

export async function loginRequest(credentials) {
  const response = await http.post('/api/v1/auth/login', credentials)
  return response.data
}

export async function getCurrentUser() {
  const response = await http.get('/api/v1/auth/me')
  return response.data
}
