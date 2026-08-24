<script setup>
defineProps({
  equipmentName: { type: String, required: true },
  loading: { type: Boolean, default: false },
})

defineEmits(['diagnose'])
</script>

<template>
  <el-card shadow="never" class="diagnosis-card">
    <p class="eyebrow">AI EQUIPMENT DIAGNOSIS</p>
    <h3>{{ equipmentName }} · AI 设备诊断</h3>
    <p>基于最新运行记录、温度、振动、故障次数和状态规则生成诊断建议。</p>
    <el-button type="primary" :loading="loading" :disabled="loading" @click="$emit('diagnose')">
      {{ loading ? '正在生成诊断…' : '重新诊断' }}
    </el-button>
  </el-card>
</template>

<style scoped>
.diagnosis-card { border: 1px solid #dce7f5; }.eyebrow { margin: 0; color: #397af2; font-size: 12px; font-weight: 700; letter-spacing: 1.2px; }.diagnosis-card h3 { margin: 8px 0; color: #132d4e; font-size: 24px; }.diagnosis-card p:not(.eyebrow) { margin: 0 0 18px; color: #6b7f99; line-height: 1.7; }
</style>
