<script setup>
import { computed } from 'vue'

import { resolveDomainDisplay } from '../../utils/domainDisplay'

const props = defineProps({ selectedModule: { type: Object, default: () => ({ id: 'generic' }) } })
const domain = computed(() => resolveDomainDisplay(props.selectedModule))
</script>

<template>
  <el-tag :type="domain.tagType" effect="plain">
    当前识别领域：{{ selectedModule?.name || domain.name }}（{{ domain.id }}）
  </el-tag>
</template>
