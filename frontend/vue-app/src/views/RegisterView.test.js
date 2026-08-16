import { createApp, nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const replace = vi.fn()

vi.mock('vue-router', () => ({ useRouter: () => ({ replace }) }))
vi.mock('../api/auth', () => ({ registerRequest: vi.fn() }))

import { registerRequest } from '../api/auth'
import RegisterView from './RegisterView.vue'

function mountRegisterView() {
  const host = document.createElement('div')
  document.body.appendChild(host)
  createApp(RegisterView).mount(host)
  return host
}

async function submit(host) {
  host.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
  await nextTick(); await Promise.resolve(); await nextTick()
}

describe('注册页面', () => {
  beforeEach(() => vi.clearAllMocks())
  afterEach(() => document.body.replaceChildren())

  it('正常渲染注册字段和返回登录入口', () => {
    const host = mountRegisterView()
    expect(host.textContent).toContain('注册数据分析工作台')
    expect(host.querySelector('input[type="email"]')).not.toBeNull()
    expect(host.textContent).toContain('已有账号？返回登录')
  })

  it('两次密码不一致时不调用注册接口', async () => {
    const host = mountRegisterView(); const inputs = host.querySelectorAll('input')
    ;['new_user', 'new@example.com', 'Password123', 'Different123'].forEach((value, index) => { inputs[index].value = value; inputs[index].dispatchEvent(new Event('input')) })
    await submit(host)
    expect(registerRequest).not.toHaveBeenCalled()
    expect(host.textContent).toContain('两次密码输入不一致')
  })

  it('注册成功后调用接口并跳转登录页', async () => {
    registerRequest.mockResolvedValue({ id: 1 })
    const host = mountRegisterView(); const inputs = host.querySelectorAll('input')
    ;['new_user', 'new@example.com', 'Password123', 'Password123'].forEach((value, index) => { inputs[index].value = value; inputs[index].dispatchEvent(new Event('input')) })
    await submit(host)
    expect(registerRequest).toHaveBeenCalledWith({ username: 'new_user', email: 'new@example.com', password: 'Password123' })
    expect(replace).toHaveBeenCalledWith({ name: 'login', query: { registered: '1' } })
  })

  it('展示后端返回的注册错误', async () => {
    registerRequest.mockRejectedValue(new Error('用户名已存在'))
    const host = mountRegisterView(); const inputs = host.querySelectorAll('input')
    ;['new_user', 'new@example.com', 'Password123', 'Password123'].forEach((value, index) => { inputs[index].value = value; inputs[index].dispatchEvent(new Event('input')) })
    await submit(host)
    expect(host.textContent).toContain('用户名已存在')
  })
})
