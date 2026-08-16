import { createApp, nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const replace = vi.fn()
const login = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ replace }),
  useRoute: () => ({ query: {} }),
}))
vi.mock('../stores/auth', () => ({ useAuthStore: () => ({ login }) }))

import LoginView from './LoginView.vue'

describe('登录页面', () => {
  beforeEach(() => vi.clearAllMocks())
  afterEach(() => document.body.replaceChildren())

  it('登录成功后立即通过 Vue Router 跳转 Dashboard', async () => {
    login.mockResolvedValue(undefined)
    const host = document.createElement('div')
    document.body.appendChild(host)
    const app = createApp(LoginView)
    app.component('router-link', { template: '<a><slot /></a>' })
    app.mount(host)
    const inputs = host.querySelectorAll('input')
    inputs[0].value = 'demo_user'; inputs[0].dispatchEvent(new Event('input'))
    inputs[1].value = 'Password123'; inputs[1].dispatchEvent(new Event('input'))
    host.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await nextTick(); await Promise.resolve(); await nextTick()

    expect(login).toHaveBeenCalledWith({ username: 'demo_user', password: 'Password123' })
    expect(replace).toHaveBeenCalledWith({ name: 'dashboard' })
  })
})
