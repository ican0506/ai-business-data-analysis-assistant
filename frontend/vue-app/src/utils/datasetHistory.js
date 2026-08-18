const ACTIVE_DATASET_KEY = 'ai_insight_active_dataset_id'

function userKey(userId) {
  return userId ? `${ACTIVE_DATASET_KEY}:${userId}` : null
}

export function getActiveDatasetId(userId) {
  const key = userKey(userId)
  const id = Number(key && localStorage.getItem(key))
  return Number.isInteger(id) && id > 0 ? id : null
}

export function setActiveDatasetId(userId, id) {
  const key = userKey(userId)
  if (key && id !== null && id !== undefined) localStorage.setItem(key, String(id))
}

export function clearActiveDatasetId(userId) {
  const key = userKey(userId)
  if (key) localStorage.removeItem(key)
}

export function toDatasetRecord(dataset) {
  return {
    id: Number(dataset.id), fileName: dataset.original_filename, status: dataset.status,
    rowCount: dataset.row_count, columnCount: dataset.column_count, uploadedAt: dataset.created_at,
  }
}

export function datasetLabel(dataset) {
  const timestamp = dataset.uploadedAt
    ? new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short', hour12: false }).format(new Date(dataset.uploadedAt))
    : '--'
  return `${dataset.fileName} · 数据集 #${dataset.id} · ${timestamp}`
}
