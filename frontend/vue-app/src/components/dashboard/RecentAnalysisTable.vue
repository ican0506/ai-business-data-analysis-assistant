<script setup>
defineProps({ rows: { type: Array, required: true } })

function statusType(status) {
  return status === '已完成' ? 'success' : 'warning'
}
</script>

<template>
  <el-table :data="rows" class="recent-analysis-table" stripe>
    <el-table-column prop="fileName" label="文件名称" min-width="300" />
    <el-table-column prop="analyzedAt" label="分析时间" width="180" />
    <el-table-column label="分析状态" width="120">
      <template #default="scope"><el-tag :type="statusType(scope.row.status)" effect="light">{{ scope.row.status }}</el-tag></template>
    </el-table-column>
  </el-table>
</template>
