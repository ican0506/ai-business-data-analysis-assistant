<script setup>
defineProps({ records: { type: Array, required: true }, cleaningId: { type: Number, default: null } })
const emit = defineEmits(['clean', 'detail', 'analyze', 'mapping'])

function statusText(status) { return { UPLOADED: '待清洗', CLEANING: '清洗中', CLEANED: '已清洗', FAILED: '处理失败' }[status] || status }
function statusType(status) { return { UPLOADED: 'info', CLEANING: 'warning', CLEANED: 'success', FAILED: 'danger' }[status] || 'info' }
</script>

<template>
  <el-card class="dataset-list-card" shadow="never">
    <template #header><div class="panel-title"><div><strong>当前用户数据集</strong><span>列表由后端实时读取，仅展示当前登录用户的数据集。</span></div><el-tag size="small" type="success">MySQL</el-tag></div></template>
    <el-empty v-if="!records.length" description="暂无数据集，请先上传 CSV 或 Excel 文件。" :image-size="92" />
    <el-table v-else :data="records" class="dataset-history-table">
      <el-table-column prop="fileName" label="文件名称" min-width="260" />
      <el-table-column prop="id" label="数据集 ID" width="110"><template #default="scope">#{{ scope.row.id }}</template></el-table-column>
      <el-table-column prop="uploadedAt" label="上传时间" width="180" />
      <el-table-column label="数据规模" width="140"><template #default="scope">{{ scope.row.rowCount ?? '--' }} 行 / {{ scope.row.columnCount ?? '--' }} 列</template></el-table-column>
      <el-table-column label="当前状态" width="120"><template #default="scope"><el-tag :type="statusType(scope.row.status)" effect="light">{{ statusText(scope.row.status) }}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="300" fixed="right"><template #default="scope"><el-button link type="primary" @click="emit('detail', scope.row)">查看详情</el-button><el-button link type="success" :loading="cleaningId === scope.row.id" :disabled="scope.row.status === 'CLEANING'" @click="emit('clean', scope.row)">开始清洗</el-button><el-button link type="primary" :disabled="scope.row.status !== 'CLEANED'" @click="emit('analyze', scope.row)">分析工作区</el-button><el-button link :disabled="scope.row.status !== 'CLEANED'" @click="emit('mapping', scope.row)">字段映射</el-button></template></el-table-column>
    </el-table>
  </el-card>
</template>
