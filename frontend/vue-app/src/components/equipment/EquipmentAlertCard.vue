<script setup>
defineProps({ alerts: { type: Array, default: () => [] } })

function severityType(severity) { return severity === '高' ? 'danger' : 'warning' }
</script>

<template>
  <el-card shadow="never" class="alert-panel">
    <template #header><div class="card-header"><strong>异常告警</strong><el-tag type="danger" effect="light">{{ alerts.length }} 条</el-tag></div></template>
    <el-empty v-if="!alerts.length" description="当前最新设备记录未触发异常规则" :image-size="72" />
    <div v-else class="alert-list">
      <article v-for="alert in alerts" :key="`${alert.equipment_name}-${alert.rule_id}`" class="alert-item">
        <el-tag :type="severityType(alert.severity)" effect="dark">{{ alert.severity }}风险</el-tag>
        <div><strong>{{ alert.equipment_name }}</strong><p>{{ alert.message }}</p><small>{{ alert.date }} · {{ alert.rule_id }}</small></div>
      </article>
    </div>
  </el-card>
</template>

<style scoped>
.alert-panel { border-color: #f2d6d1; }.card-header { display: flex; justify-content: space-between; align-items: center; }.alert-list { display: grid; gap: 12px; }.alert-item { display: flex; gap: 10px; padding: 12px; border-radius: 8px; background: #fff8f6; }.alert-item p { margin: 5px 0; color: #65758b; }.alert-item small { color: #8b9ab0; }
</style>
