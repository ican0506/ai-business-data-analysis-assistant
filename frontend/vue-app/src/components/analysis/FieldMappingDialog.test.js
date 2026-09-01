import { createApp, h } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import FieldMappingDialog from './FieldMappingDialog.vue'

let renderedRows = []
const TableStub = {
  props: ['data'],
  setup(props, { slots }) {
    return () => {
      renderedRows = props.data || []
      return h('div', { class: 'mapping-table-stub' }, slots.default?.())
    }
  },
}
const TableColumnStub = {
  props: ['prop'],
  setup(props, { slots }) {
    return () => h('div', renderedRows.map((row) => (
      props.prop === 'source' ? h('span', row.source) : slots.default?.({ row })
    )))
  },
}

function mountDialog(mapping) {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const app = createApp(FieldMappingDialog, { modelValue: true, mapping, saving: false })
  app.component('el-dialog', { template: '<div><slot /><slot name="footer" /></div>' })
  app.component('el-alert', { template: '<div><slot /></div>' })
  app.component('el-table', TableStub)
  app.component('el-table-column', TableColumnStub)
  app.component('el-tag', { template: '<span><slot /></span>' })
  app.component('el-select', { template: '<select><slot /></select>' })
  app.component('el-option-group', { template: '<optgroup><slot /></optgroup>' })
  app.component('el-option', { template: '<option />' })
  app.component('el-button', { template: '<button><slot /></button>' })
  app.mount(host)
  return host
}

describe('FieldMappingDialog', () => {
  afterEach(() => document.body.replaceChildren())

  it('展示服务端返回的所有源字段，而不是仅展示映射成功和未识别字段', () => {
    const fields = [
      ['order_id', 'order_id', 'canonical'], ['order_date', 'date', 'automatic'],
      ['product_name', 'product', 'automatic'], ['category', 'category', 'canonical'],
      ['region', 'region', 'canonical'], ['unit_price', 'unit_price', 'canonical'],
      ['quantity', 'quantity', 'canonical'], ['discount', 'discount', 'canonical'],
      ['order_amount', 'sales_amount', 'automatic'],
    ].map(([source, target, method]) => ({ source, target, method }))
    const host = mountDialog({
      overrides: {},
      field_mapping: {
        mappings: [{ source: 'order_amount', target: 'sales_amount', method: 'automatic' }],
        unmapped_columns: [],
        conflicts: [],
        fields,
      },
    })

    for (const field of fields) expect(host.textContent).toContain(field.source)
    expect(host.textContent).toContain('order_id')
    expect(host.textContent).toContain('sales_amount')
  })
})
