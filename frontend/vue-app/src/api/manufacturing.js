import http from './http'

export async function getProductionRecords() {
  const response = await http.get('/api/v1/production-records')
  return response.data
}

export async function getEquipmentRecords() {
  const response = await http.get('/api/v1/equipment-records')
  return response.data
}

export async function getEnergyRecords() {
  const response = await http.get('/api/v1/energy-records')
  return response.data
}

export async function listManufacturingReports() {
  const response = await http.get('/api/v1/manufacturing-reports')
  return response.data
}

export async function createManufacturingReport(payload = {}) {
  const response = await http.post('/api/v1/manufacturing-reports', payload)
  return response.data
}

export async function getManufacturingReport(reportId) {
  const response = await http.get(`/api/v1/manufacturing-reports/${reportId}`)
  return response.data
}

export async function downloadManufacturingReport(reportId, reportFormat) {
  return http.get(`/api/v1/manufacturing-reports/${reportId}/export/${reportFormat}`, {
    responseType: 'blob',
    returnRawResponse: true,
  })
}

export async function createPrediction(payload) {
  const response = await http.post('/api/v1/manufacturing-predictions', payload)
  return response.data
}

export async function getPredictions(params = {}) {
  const response = await http.get('/api/v1/manufacturing-predictions', { params })
  return response.data
}

export async function getPredictionDetail(predictionId) {
  const response = await http.get(`/api/v1/manufacturing-predictions/${predictionId}`)
  return response.data
}
