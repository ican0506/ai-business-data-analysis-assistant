import { createApp, nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../api/datasets', () => ({ getDatasets: vi.fn() }))
vi.mock('../api/dataChat', () => ({ queryDataChat: vi.fn() }))
vi.mock('element-plus', () => ({ ElMessage: { warning: vi.fn() } }))

import { getDatasets } from '../api/datasets'
import { queryDataChat } from '../api/dataChat'
import DataChatView from './DataChatView.vue'

const ContainerStub = { template: '<div><slot /><slot name="header" /></div>' }
const ButtonStub = { props: ['disabled', 'loading'], emits: ['click'], template: '<button :disabled="disabled" @click="$emit(\'click\')"><slot /></button>' }
const InputStub = { props: ['modelValue', 'disabled'], emits: ['update:modelValue', 'keydown'], template: '<textarea :disabled="disabled" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" @keydown="$emit(\'keydown\', $event)" />' }
const SelectStub = { props: ['modelValue'], emits: ['update:modelValue'], template: '<select :value="modelValue" @change="$emit(\'update:modelValue\', Number($event.target.value))"><slot /></select>' }

async function flush() { await Promise.resolve(); await nextTick(); await Promise.resolve(); await nextTick() }

function createDeferred() {
  let resolve
  let reject
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise
    reject = rejectPromise
  })
  return { promise, resolve, reject }
}

function mountView() {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const app = createApp(DataChatView)
  app.component('el-card', ContainerStub)
  app.component('el-empty', ContainerStub)
  app.component('el-alert', { props: ['title'], template: '<div>错误 {{ title }}<slot /></div>' })
  app.component('el-button', ButtonStub)
  app.component('el-input', InputStub)
  app.component('el-select', SelectStub)
  app.component('el-option', { props: ['label', 'value'], template: '<option :value="value">{{ label }}</option>' })
  app.component('el-tag', ContainerStub)
  app.component('el-collapse', ContainerStub)
  app.component('el-collapse-item', { props: ['title'], template: '<details><summary>{{ title }}</summary><slot /></details>' })
  app.mount(host)
  return host
}

describe('DataChatView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
    getDatasets.mockResolvedValue([{ id: 7, original_filename: 'orders_2026.xlsx' }])
  })
  afterEach(() => document.body.replaceChildren())

  it('加载数据集，未选择数据集时不发送请求', async () => {
    const host = mountView()
    await flush()

    expect(getDatasets).toHaveBeenCalledOnce()
    expect(host.querySelector('select')).not.toBeNull()
    const send = [...host.querySelectorAll('button')].find((item) => item.textContent.includes('发送'))
    expect(send.disabled).toBe(true)
    expect(queryDataChat).not.toHaveBeenCalled()
  })

  it('发送问题后展示用户消息、AI 回答和数据依据', async () => {
    queryDataChat.mockResolvedValue({
      question: '5月销售额是多少？', dataset: { id: 7, original_filename: 'orders_2026.xlsx' },
      query_plan: { metrics: ['sales_amount'], date_range: { start: '2026-05-01', end: '2026-05-31' }, group_by: [], filters: {} },
      result: { metrics: { sales_amount: 328560.5 }, data_scope: { row_count: 12 } },
      interpreter_mode: 'rule', answer: '2026年5月销售总额为328,560.50元。', answer_mode: 'deepseek',
    })
    const host = mountView()
    await flush()

    const select = host.querySelector('select')
    select.value = '7'; select.dispatchEvent(new Event('change')); await flush()
    const input = host.querySelector('textarea')
    input.value = '5月销售额是多少？'; input.dispatchEvent(new Event('input')); await flush()
    const send = [...host.querySelectorAll('button')].find((item) => item.textContent.includes('发送'))
    send.click()
    await flush()

    expect(queryDataChat).toHaveBeenCalledWith({ dataset_id: 7, question: '5月销售额是多少？' })
    expect(host.textContent).toContain('2026年5月销售总额为328,560.50元。')
    expect(host.textContent).toContain('数据依据')
    expect(host.textContent).toContain('AI 解释')
    expect(host.querySelectorAll('.message-row.user')).toHaveLength(1)
    expect(host.querySelector('.message-row.user .message')).not.toBeNull()
    expect(sessionStorage.getItem('data-chat-messages:7')).toContain('5月销售额是多少？')
  })

  it('请求期间以单条 AI loading 气泡展示，成功后替换为真实回答', async () => {
    const deferred = createDeferred()
    queryDataChat.mockReturnValue(deferred.promise)
    const host = mountView()
    await flush()

    const select = host.querySelector('select')
    select.value = '7'; select.dispatchEvent(new Event('change')); await flush()
    const input = host.querySelector('textarea')
    input.value = '5月销售额是多少？'; input.dispatchEvent(new Event('input')); await flush()
    const send = [...host.querySelectorAll('button')].find((item) => item.textContent.includes('发送'))
    send.click(); await flush()

    expect(host.querySelectorAll('.message-row.assistant .message.loading')).toHaveLength(1)
    expect(host.textContent).toContain('正在分析数据')
    expect(host.querySelector('.thinking')).toBeNull()
    expect(send.disabled).toBe(true)
    expect(queryDataChat).toHaveBeenCalledOnce()
    expect(host.querySelector('.message-row.user')).not.toBeNull()

    deferred.resolve({
      dataset: { id: 7, original_filename: 'orders_2026.xlsx' },
      query_plan: { metrics: ['sales_amount'], filters: {} },
      result: { metrics: { sales_amount: 20 } },
      interpreter_mode: 'rule', answer: '销售总额为20.00元。', answer_mode: 'rule_based',
    })
    await flush()

    expect(host.querySelectorAll('.message-row.assistant .message.loading')).toHaveLength(0)
    expect(host.textContent).toContain('销售总额为20.00元。')
  })

  it('请求失败后移除 loading 气泡，不遗留分析中提示', async () => {
    const deferred = createDeferred()
    queryDataChat.mockReturnValue(deferred.promise)
    const host = mountView()
    await flush()

    const select = host.querySelector('select')
    select.value = '7'; select.dispatchEvent(new Event('change')); await flush()
    const input = host.querySelector('textarea')
    input.value = '无法回答的问题'; input.dispatchEvent(new Event('input')); await flush()
    const send = [...host.querySelectorAll('button')].find((item) => item.textContent.includes('发送'))
    send.click(); await flush()
    expect(host.querySelectorAll('.message-row.assistant .message.loading')).toHaveLength(1)

    deferred.reject(new Error('请求失败'))
    await flush()

    expect(host.querySelectorAll('.message-row.assistant .message.loading')).toHaveLength(0)
    expect(host.textContent).not.toContain('正在分析数据')
    expect(host.textContent).toContain('请求失败')
  })

  it('推荐问题会填入输入框，后端错误会展示', async () => {
    queryDataChat.mockRejectedValue(new Error('当前数据集尚未完成清洗'))
    const host = mountView()
    await flush()
    const suggestion = [...host.querySelectorAll('button')].find((item) => item.textContent.includes('5月份销售总额'))
    suggestion.click()
    await flush()
    expect(host.querySelector('textarea').value).toContain('5月份销售总额')

    const select = host.querySelector('select')
    select.value = '7'; select.dispatchEvent(new Event('change')); await flush()
    const send = [...host.querySelectorAll('button')].find((item) => item.textContent.includes('发送'))
    send.click(); await flush()
    expect(host.textContent).toContain('当前数据集尚未完成清洗')
  })

  it('恢复最近选择的数据集及其会话，不重新调用问答接口', async () => {
    sessionStorage.setItem('data-chat-selected-dataset', '7')
    sessionStorage.setItem('data-chat-messages:7', JSON.stringify([
      { role: 'user', content: '5月销售额是多少？' },
      { role: 'assistant', content: '销售总额为20.00元。', evidence: { dataset: { original_filename: 'orders_2026.xlsx' }, query_plan: { metrics: ['sales_amount'], filters: {} }, result: { metrics: { sales_amount: 20 } }, interpreter_mode: 'rule', answer_mode: 'rule_based' } },
    ]))
    const host = mountView()
    await flush()

    expect(host.querySelector('select').value).toBe('7')
    expect(host.textContent).toContain('销售总额为20.00元。')
    expect(queryDataChat).not.toHaveBeenCalled()
  })

  it('按数据集隔离会话，并且只清空当前数据集', async () => {
    getDatasets.mockResolvedValue([{ id: 8, original_filename: 'A.xlsx' }, { id: 9, original_filename: 'B.xlsx' }])
    sessionStorage.setItem('data-chat-selected-dataset', '8')
    sessionStorage.setItem('data-chat-messages:8', JSON.stringify([{ role: 'user', content: '数据集A问题' }]))
    sessionStorage.setItem('data-chat-messages:9', JSON.stringify([{ role: 'user', content: '数据集B问题' }]))
    const host = mountView()
    await flush()

    expect(host.textContent).toContain('数据集A问题')
    const select = host.querySelector('select')
    select.value = '9'; select.dispatchEvent(new Event('change')); await flush()
    expect(host.textContent).toContain('数据集B问题')
    const clear = [...host.querySelectorAll('button')].find((item) => item.textContent.includes('清空对话'))
    clear.click(); await flush()
    expect(sessionStorage.getItem('data-chat-messages:9')).toBeNull()
    expect(sessionStorage.getItem('data-chat-messages:8')).toContain('数据集A问题')
  })

  it('遇到损坏的会话缓存时安全回退为空状态', async () => {
    sessionStorage.setItem('data-chat-selected-dataset', '7')
    sessionStorage.setItem('data-chat-messages:7', '{invalid json')
    const host = mountView()
    await flush()

    expect(host.textContent).toContain('5月份销售总额是多少？')
    expect(sessionStorage.getItem('data-chat-messages:7')).toBeNull()
  })

  it('最近数据集已失效时清除选择缓存而不继续使用', async () => {
    sessionStorage.setItem('data-chat-selected-dataset', '999')
    const host = mountView()
    await flush()

    expect(host.querySelector('select').value).toBe('')
    expect(sessionStorage.getItem('data-chat-selected-dataset')).toBeNull()
  })
})
