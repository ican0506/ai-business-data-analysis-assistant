const SELECTED_DATASET_KEY = 'data-chat-selected-dataset'
const messageKey = (datasetId) => `data-chat-messages:${datasetId}`

export function loadSelectedDataChatDataset() {
  const value = Number(sessionStorage.getItem(SELECTED_DATASET_KEY))
  return Number.isInteger(value) && value > 0 ? value : null
}

export function saveSelectedDataChatDataset(datasetId) {
  if (datasetId) sessionStorage.setItem(SELECTED_DATASET_KEY, String(datasetId))
}

export function clearSelectedDataChatDataset() {
  sessionStorage.removeItem(SELECTED_DATASET_KEY)
}

export function loadDataChatMessages(datasetId) {
  if (!datasetId) return []
  const key = messageKey(datasetId)
  try {
    const value = JSON.parse(sessionStorage.getItem(key) || '[]')
    if (!Array.isArray(value) || value.some((message) => !message || !['user', 'assistant'].includes(message.role) || typeof message.content !== 'string')) {
      throw new Error('invalid message cache')
    }
    return value
  } catch {
    sessionStorage.removeItem(key)
    return []
  }
}

export function saveDataChatMessages(datasetId, messages) {
  if (datasetId) sessionStorage.setItem(messageKey(datasetId), JSON.stringify(messages))
}

export function clearDataChatMessages(datasetId) {
  if (datasetId) sessionStorage.removeItem(messageKey(datasetId))
}
