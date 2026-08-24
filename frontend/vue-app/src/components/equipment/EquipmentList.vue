<script setup>
defineProps({
  items: { type: Array, default: () => [] },
  selectedName: { type: String, default: '' },
  loading: { type: Boolean, default: false },
})
defineEmits(['select'])

function statusType(status) {
  return status === '运行' ? 'success' : status === '停机' ? 'danger' : 'warning'
}
</script>

<template>
  <el-card shadow="never" class="equipment-list-panel">
    <template #header><strong>设备列表</strong></template>
    <el-table :data="items" v-loading="loading" row-key="equipment_name" highlight-current-row :current-row-key="selectedName" @row-click="(row) => $emit('select', row.equipment_name)">
      <el-table-column prop="equipment_name" label="设备名称" min-width="120" />
      <el-table-column prop="status" label="状态" width="92"><template #default="{ row }"><el-tag :type="statusType(row.status)" effect="light">{{ row.status }}</el-tag></template></el-table-column>
      <el-table-column prop="running_hours" label="运行时长" width="106"><template #default="{ row }">{{ row.running_hours }} h</template></el-table-column>
      <el-table-column prop="temperature" label="温度" width="92"><template #default="{ row }">{{ row.temperature }} ℃</template></el-table-column>
      <el-table-column prop="vibration" label="振动" width="92" />
    </el-table>
  </el-card>
</template>

<style scoped>
.equipment-list-panel { border-color: #e7edf5; }
</style>
