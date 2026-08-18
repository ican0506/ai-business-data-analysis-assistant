const STORAGE_KEY = 'ai_insight_analysis_history'

function storageKey(userId) { return userId ? `${STORAGE_KEY}:${userId}` : null }

function loadAll(userId) {
  const key = storageKey(userId)
  if (!key) return []
  try {
    const history = JSON.parse(localStorage.getItem(key) || '[]')
    return Array.isArray(history) ? history : []
  } catch {
    return []
  }
}

export function loadAnalysisResult(userId, datasetId) {
  return loadAll(userId).find((item) => item.datasetId === Number(datasetId)) || null
}

export function saveAnalysisResult(userId, datasetId, report) {
  const key = storageKey(userId)
  if (!key) return null
  const entry = { datasetId: Number(datasetId), report, analyzedAt: new Date().toISOString() }
  const history = loadAll(userId).filter((item) => item.datasetId !== entry.datasetId)
  history.unshift(entry)
  localStorage.setItem(key, JSON.stringify(history.slice(0, 10)))
  return entry
}
