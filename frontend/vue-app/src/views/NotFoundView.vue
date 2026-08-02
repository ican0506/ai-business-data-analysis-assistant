<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>
<template><section class="not-found-view"><el-result icon="warning" title="404" sub-title="你访问的页面不存在或已被移动。"><template #extra><el-button type="primary" @click="router.push('/dashboard')">返回数据驾驶舱</el-button></template></el-result></section></template>
