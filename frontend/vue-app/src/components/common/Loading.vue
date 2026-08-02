<script setup>
defineProps({ fullscreen: Boolean, text: { type: String, default: '正在加载，请稍候…' } })
</script>
<template><div :class="['common-loading', { fullscreen }]" role="status"><el-icon class="is-loading"><Loading /></el-icon><span>{{ text }}</span></div></template>
