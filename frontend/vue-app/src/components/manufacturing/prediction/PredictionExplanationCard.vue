<script setup>
import { computed } from 'vue'

const props = defineProps({
  explanation: { type: Object, default: null },
})

const hasExplanation = computed(() => Boolean(
  props.explanation
  && (props.explanation.summary || props.explanation.risk_explanation || props.explanation.suggestions?.length),
))

const modeLabel = computed(() => (
  props.explanation?.mode === 'deepseek' ? 'DeepSeek 解释' : '规则降级'
))

const modeTagType = computed(() => (
  props.explanation?.mode === 'deepseek' ? 'success' : 'info'
))
</script>

<template>
  <el-card shadow="never" class="prediction-explanation-card">
    <template #header>
      <div class="card-header">
        <div>
          <p class="eyebrow">AI PREDICTION EXPLANATION</p>
          <strong>AI 预测解释</strong>
        </div>
        <el-tag v-if="hasExplanation" :type="modeTagType" effect="plain">{{ modeLabel }}</el-tag>
      </div>
    </template>

    <el-empty
      v-if="!hasExplanation"
      description="暂无 AI 预测解释，预测结果仍可正常查看。"
      :image-size="72"
    />
    <div v-else class="explanation-content">
      <section v-if="explanation.summary" class="explanation-section">
        <h4>AI 总结</h4>
        <p>{{ explanation.summary }}</p>
      </section>
      <section v-if="explanation.risk_explanation" class="explanation-section risk-section">
        <h4>风险解释</h4>
        <p>{{ explanation.risk_explanation }}</p>
      </section>
      <section v-if="explanation.suggestions?.length" class="explanation-section suggestion-section">
        <h4>处理建议</h4>
        <ol>
          <li v-for="suggestion in explanation.suggestions" :key="suggestion">{{ suggestion }}</li>
        </ol>
      </section>
    </div>
  </el-card>
</template>

<style scoped>
.prediction-explanation-card { border: 1px solid #dce7f5; }
.card-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.eyebrow { margin: 0 0 5px; color: #397af2; font-size: 12px; font-weight: 700; letter-spacing: 1.2px; }
.card-header strong { color: #173658; font-size: 17px; }
.explanation-content { display: grid; gap: 16px; }
.explanation-section { padding: 14px 16px; border-radius: 8px; background: #f7faff; }
.risk-section { border-left: 3px solid #f3a33a; }
.suggestion-section { border-left: 3px solid #37a879; }
.explanation-section h4 { margin: 0 0 8px; color: #264769; font-size: 14px; }
.explanation-section p { margin: 0; color: #59708a; line-height: 1.75; white-space: pre-line; }
.explanation-section ol { display: grid; gap: 7px; margin: 0; padding-left: 20px; color: #3d6d59; line-height: 1.65; }
</style>
