<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const form = reactive({ username: '', password: '' })
const errorMessage = ref('')
const isSubmitting = ref(false)
const successMessage = computed(() => route.query.registered === '1' ? '注册成功，请登录' : '')

async function submitLogin() {
  errorMessage.value = ''
  isSubmitting.value = true
  try {
    await auth.login(form)
    await router.replace({ name: 'dashboard' })
  } catch (error) {
    errorMessage.value = error.message || '登录失败，请检查账号和密码'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-card" aria-labelledby="login-title">
      <p class="brand">AI <span>Insight</span></p>
      <p class="eyebrow">BUSINESS INTELLIGENCE PLATFORM</p>
      <h1 id="login-title">登录数据分析工作台</h1>
      <p class="description">上传业务数据，生成指标洞察与 AI 分析报告。</p>

      <form @submit.prevent="submitLogin">
        <label>
          用户名
          <input v-model.trim="form.username" autocomplete="username" required placeholder="请输入用户名" />
        </label>
        <label>
          密码
          <input v-model="form.password" type="password" autocomplete="current-password" required placeholder="请输入密码" />
        </label>
        <p v-if="errorMessage" class="form-error" role="alert">{{ errorMessage }}</p>
        <p v-if="successMessage" class="form-success" role="status">{{ successMessage }}</p>
        <button type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? '正在登录…' : '登录工作台' }}
        </button>
        <p class="auth-switch">还没有账号？<router-link :to="{ name: 'register' }">立即注册</router-link></p>
      </form>
    </section>
  </main>
</template>
