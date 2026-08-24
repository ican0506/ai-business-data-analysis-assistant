<script setup>
defineProps({ record: { type: Object, default: null } })
</script>

<template>
  <el-card shadow="never" class="equipment-detail-panel">
    <template #header><strong>设备详情</strong></template>
    <el-empty v-if="!record" description="请选择设备查看详情" :image-size="72" />
    <el-descriptions v-else :column="2" border>
      <el-descriptions-item label="设备名称">{{ record.equipment_name }}</el-descriptions-item>
      <el-descriptions-item label="记录日期">{{ record.date }}</el-descriptions-item>
      <el-descriptions-item label="运行状态"><el-tag :type="record.status === '运行' ? 'success' : 'warning'">{{ record.status }}</el-tag></el-descriptions-item>
      <el-descriptions-item label="运行时长">{{ record.running_hours }} h</el-descriptions-item>
      <el-descriptions-item label="故障次数">{{ record.fault_count }} 次</el-descriptions-item>
      <el-descriptions-item label="温度">{{ record.temperature }} ℃</el-descriptions-item>
      <el-descriptions-item label="振动值">{{ record.vibration }}</el-descriptions-item>
    </el-descriptions>
  </el-card>
</template>

<style scoped>
.equipment-detail-panel { border-color: #e7edf5; }
</style>
