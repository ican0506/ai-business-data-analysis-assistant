const STORAGE_KEY = 'ai_insight_dataset_history'

export function loadDatasetHistory() {
  try {
    const records = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    return Array.isArray(records) ? records : []
  } catch {
    return []
  }
}

function save(records) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(records))
}

export function addDatasetRecord(record) {
  const records = loadDatasetHistory().filter((item) => item.id !== record.id)
  records.unshift(record)
  save(records)
  return records
}

export function updateDatasetRecord(id, patch) {
  const records = loadDatasetHistory().map((item) => (item.id === id ? { ...item, ...patch } : item))
  save(records)
  return records
}
