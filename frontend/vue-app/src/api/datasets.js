import http from './http'

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

export async function analyzeDataset(datasetId) {
  const response = await http.post(`/api/v1/datasets/${datasetId}/ai-analysis`)
  return response.data
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
  const response = await http.get(path, { responseType: 'blob', returnRawResponse: true })
  const disposition = response.headers['content-disposition'] || ''
  const match = disposition.match(/filename\*?=(?:UTF-8''|\")?([^;\"]+)/i)
  return {
    blob: response.data,
    filename: match ? decodeURIComponent(match[1].trim()) : null,
  }
}
