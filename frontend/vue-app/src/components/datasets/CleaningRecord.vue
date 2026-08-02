<script setup>
defineProps({ record: { type: Object, default: null } })
</script>

<template>
  <el-card class="cleaning-record-card" shadow="never"><template #header><div class="panel-title"><div><strong>最近清洗结果</strong><span>展示本页面最近一次成功的真实清洗响应。</span></div></div></template><el-empty v-if="!record" description="尚未执行清洗操作" :image-size="72" /><el-descriptions v-else :column="2" border><el-descriptions-item label="数据集">{{ record.fileName }}</el-descriptions-item><el-descriptions-item label="清洗任务 ID">{{ record.cleaningRunId }}</el-descriptions-item><el-descriptions-item label="原始行数">{{ record.sourceRowCount }}</el-descriptions-item><el-descriptions-item label="清洗后行数">{{ record.cleanedRowCount }}</el-descriptions-item><el-descriptions-item label="移除空值行">{{ record.removedEmptyRows }}</el-descriptions-item><el-descriptions-item label="移除重复行">{{ record.removedDuplicateRows }}</el-descriptions-item></el-descriptions></el-card>
</template>
