<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from './stores/auth'

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
</script>

<template>
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
