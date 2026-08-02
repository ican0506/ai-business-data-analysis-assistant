const STORAGE_KEY = 'ai_insight_analysis_history'

function loadAll() {
  try {
    const history = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    return Array.isArray(history) ? history : []
  } catch {
    return []
  }
}

export function loadAnalysisResult(datasetId) {
  return loadAll().find((item) => item.datasetId === Number(datasetId)) || null
}

export function saveAnalysisResult(datasetId, report) {
  const entry = { datasetId: Number(datasetId), report, analyzedAt: new Date().toISOString() }
  const history = loadAll().filter((item) => item.datasetId !== entry.datasetId)
  history.unshift(entry)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(0, 10)))
  return entry
}
