<script setup>
import { computed } from 'vue'

const props = defineProps({ recommendations: { type: [Array, String], default: () => [] } })
const normalizedRecommendations = computed(() => (
  Array.isArray(props.recommendations)
    ? props.recommendations
    : props.recommendations
      ? [props.recommendations]
      : []
))
</script>

<template>
  <el-card class="report-panel suggestion-panel" shadow="never">
    <template #header><div class="report-panel-title"><span>03</span><div><strong>业务建议</strong><small>优化建议与行动方案</small></div></div></template>
    <ol class="recommendation-list"><li v-for="(item, index) in normalizedRecommendations" :key="item"><b>{{ String(index + 1).padStart(2, '0') }}</b><span>{{ item }}</span></li></ol>
  </el-card>
</template>
