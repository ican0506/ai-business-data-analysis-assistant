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
})
