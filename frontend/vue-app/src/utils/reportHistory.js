const STORAGE_KEY = 'ai_insight_report_history'

function storageKey(userId) { return userId ? `${STORAGE_KEY}:${userId}` : null }

export function loadReportHistory(userId) {
  const key = storageKey(userId)
  if (!key) return []
  try {
    const records = JSON.parse(localStorage.getItem(key) || '[]')
    return Array.isArray(records) ? records : []
  } catch {
    return []
  }
}

export function saveReportRecord(userId, record) {
  const key = storageKey(userId)
  if (!key) return []
  const item = { ...record, generatedAt: new Date().toISOString(), status: 'SUCCESS' }
  const history = [item, ...loadReportHistory(userId)].slice(0, 30)
  localStorage.setItem(key, JSON.stringify(history))
  return history
}
