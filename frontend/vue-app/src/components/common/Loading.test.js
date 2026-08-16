import { createApp, nextTick, reactive } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia } from 'pinia'

const route = reactive({ meta: { public: true } })

vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => ({ replace: vi.fn() }),
}))

import App from '../../App.vue'
import Loading from './Loading.vue'
import { beginRequest, endRequest, resetRequests } from '../../utils/requestState'

const ContainerStub = { template: '<div><slot /></div>' }

function mount(component) {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const app = createApp(component)
  app.use(createPinia())
  app.component('RouterView', ContainerStub)
  app.component('el-icon', ContainerStub)
  app.component('el-container', ContainerStub)
  app.component('el-aside', ContainerStub)
  app.component('el-header', ContainerStub)
  app.component('el-main', ContainerStub)
  app.component('el-menu', ContainerStub)
  app.component('el-menu-item', ContainerStub)
  app.component('el-avatar', ContainerStub)
  app.component('el-button', ContainerStub)
  app.mount(host)
  return host
}

describe('公共 Loading 组件', () => {
  beforeEach(() => resetRequests())
  afterEach(() => document.body.replaceChildren())

  it('可以只渲染一个 spinner，不递归渲染自身', () => {
    const host = mount(Loading)

    expect(host.querySelectorAll('[role="status"]')).toHaveLength(1)
    expect(host.textContent).toContain('正在加载，请稍候…')
  })

  it('全局请求开始时 App 显示 Loading，请求结束后正常消失', async () => {
    const host = mount(App)

    expect(host.querySelector('[role="status"]')).toBeNull()
    beginRequest()
    await nextTick()
    expect(host.querySelectorAll('[role="status"]')).toHaveLength(1)

    endRequest()
    await nextTick()
    expect(host.querySelector('[role="status"]')).toBeNull()
  })
})
