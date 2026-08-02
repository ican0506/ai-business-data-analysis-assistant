<script setup>
defineProps({
  item: { type: Object, required: true },
})
</script>

<template>
  <el-card class="kpi-card" shadow="never">
    <p>{{ item.label }}</p>
    <div class="kpi-value">
      <strong>{{ item.value }}</strong><span>{{ item.suffix }}</span>
    </div>
    <el-tag size="small" effect="plain" :type="item.type">{{ item.trend }}</el-tag>
  </el-card>
</template>
