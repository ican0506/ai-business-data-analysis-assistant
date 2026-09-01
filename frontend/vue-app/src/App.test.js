import { createApp } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('vue-router', () => ({
  useRoute: () => ({ name: 'DataChat', path: '/data-chat', meta: {} }),
  useRouter: () => ({ replace: vi.fn() }),
}))
vi.mock('./stores/auth', () => ({
  useAuthStore: () => ({ user: null, logout: vi.fn() }),
}))
vi.mock('./utils/requestState', async () => {
  const { ref } = await import('vue')
  return { isRequesting: ref(true) }
})

import App from './App.vue'

describe('App', () => {
  afterEach(() => document.body.replaceChildren())

  it('Data Chat 请求期间不渲染全局全屏 Loading', () => {
    const host = document.createElement('div')
    document.body.appendChild(host)
    const app = createApp(App)
    app.component('RouterView', { template: '<div>Data Chat 内容</div>' })
    app.component('Loading', { template: '<div data-testid="global-loading" />' })
    app.component('el-container', { template: '<div><slot /></div>' })
    app.component('el-aside', { template: '<aside><slot /></aside>' })
    app.component('el-header', { template: '<header><slot /></header>' })
    app.component('el-main', { template: '<main><slot /></main>' })
    app.component('el-menu', { template: '<nav><slot /></nav>' })
    app.component('el-menu-item', { template: '<div><slot /></div>' })
    app.component('el-avatar', { template: '<span><slot /></span>' })
    app.component('el-button', { template: '<button><slot /></button>' })
    app.mount(host)

    expect(host.querySelector('[data-testid="global-loading"]')).toBeNull()
    expect(host.textContent).toContain('Data Chat 内容')
  })
})
