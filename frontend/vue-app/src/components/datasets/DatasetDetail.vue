<script setup>
defineProps({ modelValue: { type: Boolean, required: true }, dataset: { type: Object, default: null } })
defineEmits(['update:modelValue'])
</script>

<template>
  <el-dialog :model-value="modelValue" title="数据集详情" width="720px" @update:model-value="$emit('update:modelValue', $event)">
    <template v-if="dataset"><el-descriptions :column="2" border><el-descriptions-item label="文件名称">{{ dataset.fileName }}</el-descriptions-item><el-descriptions-item label="后端数据集 ID">{{ dataset.id }}</el-descriptions-item><el-descriptions-item label="行数">{{ dataset.rowCount }}</el-descriptions-item><el-descriptions-item label="列数">{{ dataset.columnCount }}</el-descriptions-item></el-descriptions><h4 class="detail-heading">字段识别结果</h4><el-table :data="dataset.columns || []" max-height="260"><el-table-column prop="name" label="字段" /><el-table-column prop="data_type" label="类型" /><el-table-column prop="missing_count" label="缺失值" /><el-table-column prop="unique_count" label="唯一值" /></el-table></template>
    <el-empty v-else description="请选择数据集" />
  </el-dialog>
</template>
