<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { registerRequest } from '../api/auth'

const router = useRouter()
const form = reactive({ username: '', email: '', password: '', confirmPassword: '' })
const errorMessage = ref('')
const isSubmitting = ref(false)

function validateForm() {
  if (form.username.length < 3) return '用户名至少需要 3 个字符'
  if (!/^\S+@\S+\.\S+$/.test(form.email)) return '请输入合法的邮箱地址'
  if (form.password.length < 8) return '密码至少需要 8 个字符'
  if (form.password !== form.confirmPassword) return '两次密码输入不一致'
  return ''
}

async function submitRegister() {
  errorMessage.value = validateForm()
  if (errorMessage.value) return
  isSubmitting.value = true
  try {
    await registerRequest({ username: form.username, email: form.email, password: form.password })
    await router.replace({ name: 'login', query: { registered: '1' } })
  } catch (error) {
    errorMessage.value = error.message || '注册失败，请稍后重试'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-card" aria-labelledby="register-title">
      <p class="brand">AI <span>Insight</span></p>
      <p class="eyebrow">BUSINESS INTELLIGENCE PLATFORM</p>
      <h1 id="register-title">注册数据分析工作台</h1>
      <p class="description">创建账号后即可上传业务数据，获取指标洞察与 AI 分析报告。</p>

      <form @submit.prevent="submitRegister">
        <label>用户名<input v-model.trim="form.username" autocomplete="username" required minlength="3" maxlength="50" placeholder="3～50 个字符" /></label>
        <label>邮箱<input v-model.trim="form.email" type="email" autocomplete="email" required placeholder="请输入邮箱地址" /></label>
        <label>密码<input v-model="form.password" type="password" autocomplete="new-password" required minlength="8" maxlength="72" placeholder="8～72 个字符" /></label>
        <label>确认密码<input v-model="form.confirmPassword" type="password" autocomplete="new-password" required placeholder="请再次输入密码" /></label>
        <p v-if="errorMessage" class="form-error" role="alert">{{ errorMessage }}</p>
        <button type="submit" :disabled="isSubmitting">{{ isSubmitting ? '正在注册…' : '注册账号' }}</button>
        <p class="auth-switch">已有账号？<button type="button" class="auth-link" @click="router.replace({ name: 'login' })">返回登录</button></p>
      </form>
    </section>
  </main>
</template>
