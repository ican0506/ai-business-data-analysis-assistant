<script setup>
defineProps({ records: { type: Array, required: true }, cleaningId: { type: Number, default: null } })
const emit = defineEmits(['clean', 'detail', 'analyze', 'mapping'])

function readableSize(size = 0) { return size < 1024 * 1024 ? `${(size / 1024).toFixed(1)} KB` : `${(size / 1024 / 1024).toFixed(2)} MB` }
function statusText(status) { return { UPLOADED: '待清洗', CLEANING: '清洗中', CLEANED: '已清洗', FAILED: '处理失败' }[status] || status }
function statusType(status) { return { UPLOADED: 'info', CLEANING: 'warning', CLEANED: 'success', FAILED: 'danger' }[status] || 'info' }
</script>

<template>
  <el-card class="dataset-list-card" shadow="never">
    <template #header><div class="panel-title"><div><strong>本机展示记录</strong><span>后端暂未提供列表接口，仅显示此浏览器成功上传过的数据集。</span></div><el-tag size="small" type="info">localStorage</el-tag></div></template>
    <el-empty v-if="!records.length" description="暂无成功上传记录" :image-size="92" />
    <el-table v-else :data="records" class="dataset-history-table">
      <el-table-column prop="fileName" label="文件名称" min-width="260" />
      <el-table-column prop="uploadedAt" label="上传时间" width="180" />
      <el-table-column label="文件大小" width="120"><template #default="scope">{{ readableSize(scope.row.fileSize) }}</template></el-table-column>
      <el-table-column label="当前状态" width="120"><template #default="scope"><el-tag :type="statusType(scope.row.status)" effect="light">{{ statusText(scope.row.status) }}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="300" fixed="right"><template #default="scope"><el-button link type="primary" @click="emit('detail', scope.row)">查看详情</el-button><el-button link type="success" :loading="cleaningId === scope.row.id" :disabled="scope.row.status === 'CLEANING'" @click="emit('clean', scope.row)">开始清洗</el-button><el-button link type="primary" :disabled="scope.row.status !== 'CLEANED'" @click="emit('analyze', scope.row)">分析工作区</el-button><el-button link :disabled="scope.row.status !== 'CLEANED'" @click="emit('mapping', scope.row)">字段映射</el-button></template></el-table-column>
    </el-table>
  </el-card>
</template>
