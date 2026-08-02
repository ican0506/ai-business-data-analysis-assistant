<script setup>
import { useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.replace({ name: 'login' })
}
</script>

<template>
  <main class="workspace-page">
    <section class="workspace-card">
      <p class="eyebrow">VUE 3 FOUNDATION READY</p>
      <h1>欢迎，{{ auth.user?.username || '用户' }}</h1>
      <p>登录认证、JWT 保存、Axios 请求封装、Vue Router 和 Pinia 状态管理已就绪。</p>
      <button type="button" class="secondary-button" @click="logout">退出登录</button>
    </section>
  </main>
</template>
