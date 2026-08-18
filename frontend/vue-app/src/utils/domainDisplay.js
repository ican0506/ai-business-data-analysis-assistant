export const DOMAIN_DISPLAY = {
  order: { id: 'order', name: '订单分析', tagType: 'primary' },
  student_score: { id: 'student_score', name: '学生成绩分析', tagType: 'success' },
  inventory: { id: 'inventory', name: '库存分析', tagType: 'warning' },
  generic: { id: 'generic', name: '通用数据分析', tagType: 'info' },
}

export const CANONICAL_FIELD_GROUPS = [
  { label: '订单', fields: ['order_id', 'product', 'quantity', 'unit_price', 'sales_amount', 'customer_id', 'customer_name', 'category', 'region', 'status', 'date', 'discount', 'payment_method', 'gender', 'age', 'target_amount'] },
  { label: '学生成绩', fields: ['student_id', 'student_name', 'subject', 'score', 'class_name', 'grade', 'exam_name', 'exam_date'] },
  { label: '库存', fields: ['product_id', 'product_name', 'category', 'stock_quantity', 'safety_stock', 'unit_cost', 'warehouse', 'supplier', 'inbound_quantity', 'outbound_quantity', 'inventory_date'] },
]

export function resolveDomainDisplay(selectedModule) {
  return DOMAIN_DISPLAY[selectedModule?.id] || DOMAIN_DISPLAY.generic
}

export function showMetricValue(value) {
  if (value === null || value === undefined) return '—'
  return typeof value === 'number' && !Number.isFinite(value) ? '—' : String(value)
}

export function formatNumber(value, maximumFractionDigits = 2) {
  const number = Number(value)
  if (value === null || value === undefined || !Number.isFinite(number)) return '—'
  return new Intl.NumberFormat('zh-CN', { maximumFractionDigits }).format(number)
}
