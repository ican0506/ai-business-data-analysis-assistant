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

export async function downloadDatasetReport(datasetId, reportType) {
  const path = reportType === 'excel'
    ? `/api/v1/datasets/${datasetId}/reports/excel`
    : `/api/v1/datasets/${datasetId}/reports/${reportType}`
  return http.get(path, { responseType: 'blob' })
}
