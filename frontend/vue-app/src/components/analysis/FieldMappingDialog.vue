<script setup>
import { computed, ref, watch } from 'vue'

import { CANONICAL_FIELD_GROUPS } from '../../utils/domainDisplay'

const props = defineProps({ modelValue: { type: Boolean, required: true }, mapping: { type: Object, default: null }, saving: Boolean })
const emit = defineEmits(['update:modelValue', 'save', 'reset'])
const overrides = ref({})
const rows = computed(() => {
  const fieldMapping = props.mapping?.field_mapping || {}
  const mappings = fieldMapping.mappings || []
  const mappedSources = new Set(mappings.map((item) => item.source))
  const result = mappings.map((item) => ({ ...item, currentTarget: item.target }))
  for (const source of fieldMapping.unmapped_columns || []) if (!mappedSources.has(source)) result.push({ source, currentTarget: null, method: 'unmapped' })
  return result
})
const conflicts = computed(() => props.mapping?.field_mapping?.conflicts || [])
watch(() => props.mapping, (mapping) => { overrides.value = { ...(mapping?.overrides || {}) } }, { immediate: true, deep: true })
function selectedOverride(source) { return overrides.value[source] || '' }
function setOverride(source, target) { const next = { ...overrides.value }; if (target) next[source] = target; else delete next[source]; overrides.value = next }
</script>

<template>
  <el-dialog :model-value="modelValue" title="字段映射" width="min(920px, 94vw)" @update:model-value="emit('update:modelValue', $event)">
    <p class="mapping-copy">映射只作用于该数据集的后端分析副本；自动识别、用户指定、未映射与冲突均以服务端结果为准。</p>
    <el-alert v-if="conflicts.length" type="warning" :closable="false" show-icon title="检测到字段映射冲突"><template #default><ul class="mapping-conflicts"><li v-for="conflict in conflicts" :key="`${conflict.target}-${conflict.reason}`">{{ conflict.target }}：{{ conflict.reason }}（{{ conflict.sources.join('、') }}）</li></ul></template></el-alert>
    <el-table :data="rows" max-height="410" class="mapping-table">
      <el-table-column prop="source" label="原始字段" min-width="160" />
      <el-table-column label="当前映射" min-width="170"><template #default="{ row }">{{ row.currentTarget || '未映射' }}</template></el-table-column>
      <el-table-column label="来源" width="115"><template #default="{ row }"><el-tag :type="row.method === 'override' ? 'success' : row.method === 'automatic' ? 'primary' : 'info'" size="small" effect="plain">{{ row.method === 'override' ? '用户指定' : row.method === 'automatic' ? '自动识别' : '未识别' }}</el-tag></template></el-table-column>
      <el-table-column label="人工修正" min-width="250"><template #default="{ row }"><el-select :model-value="selectedOverride(row.source)" clearable placeholder="保持当前自动映射" @update:model-value="setOverride(row.source, $event)"><el-option-group v-for="group in CANONICAL_FIELD_GROUPS" :key="group.label" :label="group.label"><el-option v-for="field in group.fields" :key="field" :label="field" :value="field" /></el-option-group></el-select></template></el-table-column>
    </el-table>
    <template #footer><el-button :disabled="saving" @click="emit('reset')">恢复自动映射</el-button><el-button @click="emit('update:modelValue', false)">取消</el-button><el-button type="primary" :loading="saving" @click="emit('save', overrides)">保存映射</el-button></template>
  </el-dialog>
</template>
