import http from './http'

export async function getEquipmentList() {
  const response = await http.get('/api/v1/equipment-management')
  return response.data
}

export async function getEquipmentDetail(equipmentName) {
  const response = await http.get(`/api/v1/equipment-management/${encodeURIComponent(equipmentName)}`)
  return response.data
}

export async function getEquipmentHistory(equipmentName) {
  const response = await http.get(`/api/v1/equipment-management/${encodeURIComponent(equipmentName)}/history`)
  return response.data
}

export async function getEquipmentAnomalies() {
  const response = await http.get('/api/v1/equipment-management/anomalies')
  return response.data
}
