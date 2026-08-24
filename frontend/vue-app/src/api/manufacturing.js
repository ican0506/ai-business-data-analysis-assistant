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
