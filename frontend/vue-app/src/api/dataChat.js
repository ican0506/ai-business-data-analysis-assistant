import http from './http'

export async function queryDataChat(payload) {
  const response = await http.post('/api/v1/data-chat/query', payload, {
    timeout: 60000,
    timeoutMessage: '数据问答请求超时，请稍后重试。',
  })
  return response.data
}
