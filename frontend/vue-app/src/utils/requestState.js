import { computed, ref } from 'vue'

const pendingCount = ref(0)
export const isRequesting = computed(() => pendingCount.value > 0)
export function beginRequest() { pendingCount.value += 1 }
export function endRequest() { pendingCount.value = Math.max(0, pendingCount.value - 1) }
export function resetRequests() { pendingCount.value = 0 }
