import http from './http'

const pendingAnalysisRequests = new Map()

export async function getDatasets() {
  const response = await http.get('/api/v1/datasets')
  return response.data
}

export async function uploadDataset(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)
  const response = await http.post('/api/v1/datasets/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (event) => {
      if (event.total) onProgress?.(Math.round((event.loaded / event.total) * 100))
    },
  })
  return response.data
}

export async function cleanDataset(datasetId) {
  const response = await http.post(`/api/v1/datasets/${datasetId}/clean`)
  return response.data
}

export function analyzeDataset(datasetId) {
  const existingRequest = pendingAnalysisRequests.get(datasetId)
  if (existingRequest) return existingRequest

  const request = http.post(`/api/v1/datasets/${datasetId}/ai-analysis`, null, {
    timeout: 30000,
    timeoutMessage: 'AI 服务响应较慢，请稍后重试。',
  }).then((response) => response.data)
  pendingAnalysisRequests.set(datasetId, request)
  return request.finally(() => {
    if (pendingAnalysisRequests.get(datasetId) === request) {
      pendingAnalysisRequests.delete(datasetId)
    }
  })
}

export async function getDatasetMetrics(datasetId) {
  const response = await http.get(`/api/v1/datasets/${datasetId}/metrics`)
  return response.data
}

export async function getFieldMapping(datasetId) {
  const response = await http.get(`/api/v1/datasets/${datasetId}/field-mapping`)
  return response.data
}

export async function replaceFieldMapping(datasetId, overrides) {
  const response = await http.put(`/api/v1/datasets/${datasetId}/field-mapping`, { overrides })
  return response.data
}

export async function downloadDatasetReport(datasetId, reportType) {
  const path = reportType === 'excel'
    ? `/api/v1/datasets/${datasetId}/reports/excel`
    : `/api/v1/datasets/${datasetId}/reports/${reportType}`
  const response = await http.get(path, {
    responseType: 'blob',
    returnRawResponse: true,
    timeout: 120000,
    timeoutMessage: '报告生成超时，请稍后重试。',
  })
  const disposition = response.headers['content-disposition'] || ''
  const match = disposition.match(/filename\*?=(?:UTF-8''|\")?([^;\"]+)/i)
  return {
    blob: response.data,
    filename: match ? decodeURIComponent(match[1].trim()) : null,
  }
}
