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
