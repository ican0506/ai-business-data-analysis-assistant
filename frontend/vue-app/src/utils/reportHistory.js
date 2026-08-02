const STORAGE_KEY = 'ai_insight_report_history'

export function loadReportHistory() {
  try {
    const records = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    return Array.isArray(records) ? records : []
  } catch {
    return []
  }
}

export function saveReportRecord(record) {
  const item = { ...record, generatedAt: new Date().toISOString(), status: 'SUCCESS' }
  const history = [item, ...loadReportHistory()].slice(0, 30)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history))
  return history
}
