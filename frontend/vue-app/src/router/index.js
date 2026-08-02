import { createRouter, createWebHistory } from 'vue-router'

import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import DatasetManagementView from '../views/DatasetManagementView.vue'
import AiAnalysisView from '../views/AiAnalysisView.vue'
import DownloadCenterView from '../views/DownloadCenterView.vue'
import NotFoundView from '../views/NotFoundView.vue'
import { TOKEN_STORAGE_KEY } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
    { path: '/workspace', redirect: '/dashboard' },
    { path: '/dashboard', name: 'dashboard', component: DashboardView },
    { path: '/datasets', name: 'datasets', component: DatasetManagementView },
    { path: '/ai-analysis', name: 'ai-analysis', component: AiAnalysisView },
    { path: '/downloads', name: 'downloads', component: DownloadCenterView },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView, meta: { public: true } },
  ],
})

router.beforeEach((to) => {
  const hasToken = Boolean(localStorage.getItem(TOKEN_STORAGE_KEY))
  if (!to.meta.public && !hasToken) return { name: 'login' }
  if (to.name === 'login' && hasToken) return { name: 'dashboard' }
  return true
})

export default router
