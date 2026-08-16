<script setup>
defineProps({ fullscreen: Boolean, text: { type: String, default: '正在加载，请稍候…' } })
</script>
<template>
  <div :class="['common-loading', { fullscreen }]" role="status">
    <span class="loading-spinner" aria-hidden="true" />
    <span>{{ text }}</span>
  </div>
</template>

<style scoped>
.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: loading-spin .7s linear infinite;
}

@keyframes loading-spin {
  to { transform: rotate(360deg); }
}
</style>
