<script setup>
defineProps({ title: { type: String, default: '加载失败' }, description: { type: String, default: '请检查网络后重试。' } })
defineEmits(['retry'])
</script>
<template><el-result icon="error" :title="title" :sub-title="description"><template #extra><el-button type="primary" @click="$emit('retry')">重新尝试</el-button></template></el-result></template>
