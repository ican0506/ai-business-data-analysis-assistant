<script setup>
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useAuthStore } from './stores/auth'
import Loading from './components/common/Loading.vue'
import { isRequesting } from './utils/requestState'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const isPublicPage = computed(() => route.meta.public === true)

const navigationItems = [
  { index: '/dashboard', title: '数据驾驶舱', description: '核心经营概览' },
  { index: '/datasets', title: '数据集管理', description: '上传与清洗记录' },
  { index: '/ai-analysis', title: 'AI分析报告', description: '智能业务洞察' },
  { index: '/downloads', title: '报告下载中心', description: '导出文件管理' },
]

function logout() {
  auth.logout()
  router.replace({ name: 'login' })
}

function showGlobalError(event) { ElMessage.error(event.detail || '请求失败，请稍后重试。') }
function handleSessionExpired() {
  auth.logout()
  if (route.name !== 'login') router.replace({ name: 'login' })
}
onMounted(() => window.addEventListener('app-error', showGlobalError))
onMounted(() => window.addEventListener('session-expired', handleSessionExpired))
onBeforeUnmount(() => {
  window.removeEventListener('app-error', showGlobalError)
  window.removeEventListener('session-expired', handleSessionExpired)
})
</script>

<template>
  <Loading v-if="isRequesting" fullscreen text="正在处理数据请求…" />
  <RouterView v-if="isPublicPage" />

  <el-container v-else class="app-shell">
    <el-aside class="app-sidebar" width="248px">
      <div class="brand-panel">
        <span class="brand-mark">AI</span>
        <div>
          <strong>AI 智能数据分析助手</strong>
          <small>Business Intelligence</small>
        </div>
      </div>

      <el-menu class="sidebar-menu" router :default-active="route.path">
        <el-menu-item v-for="item in navigationItems" :key="item.index" :index="item.index">
          <div class="menu-label">
            <span>{{ item.title }}</span>
            <small>{{ item.description }}</small>
          </div>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <div>
          <p class="header-kicker">ENTERPRISE DATA WORKSPACE</p>
          <h1>企业运营数据分析平台</h1>
        </div>
        <div class="user-actions">
          <el-avatar :size="34">{{ auth.user?.username?.slice(0, 1).toUpperCase() || 'U' }}</el-avatar>
          <div class="user-summary">
            <strong>{{ auth.user?.username || '当前用户' }}</strong>
            <span>{{ auth.user?.role || 'USER' }}</span>
          </div>
          <el-button plain @click="logout">退出登录</el-button>
        </div>
      </el-header>

      <el-main class="app-main">
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>
