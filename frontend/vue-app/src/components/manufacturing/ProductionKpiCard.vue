<script setup>
defineProps({
  item: { type: Object, required: true },
})
</script>

<template>
  <el-card class="production-kpi-card" shadow="never">
    <p class="kpi-label">{{ item.label }}</p>
    <div class="kpi-value">
      <strong>{{ item.value }}</strong><span>{{ item.suffix }}</span>
    </div>
    <p class="kpi-note">{{ item.note }}</p>
  </el-card>
</template>

<style scoped>
.production-kpi-card { min-height: 148px; border-color: #e7edf5; }
.kpi-label, .kpi-note { margin: 0; color: #6b7f99; }
.kpi-label { font-size: 14px; }
.kpi-value { display: flex; align-items: baseline; gap: 6px; margin: 18px 0 12px; color: #15385b; }
.kpi-value strong { font-size: 30px; line-height: 1; }
.kpi-value span { font-size: 14px; }
.kpi-note { font-size: 12px; }
</style>
