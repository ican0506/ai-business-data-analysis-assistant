export const dashboardMockData = {
  kpis: [
    { label: '数据集数量', value: 28, suffix: '个', trend: '+4 本月新增', type: 'primary' },
    { label: '分析次数', value: 186, suffix: '次', trend: '+18.6% 环比', type: 'success' },
    { label: '报告生成数量', value: 94, suffix: '份', trend: '+12 本月新增', type: 'warning' },
    { label: '最近一次分析', value: '今天 10:32', suffix: '', trend: '销售经营月度分析', type: 'info' },
  ],
  trend: {
    labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    values: [14, 19, 16, 26, 31, 22, 35],
  },
  metrics: {
    labels: ['华东', '华南', '华北', '华中', '西南'],
    values: [86, 72, 91, 68, 77],
  },
  distribution: [
    { name: '销售数据', value: 42 },
    { name: '运营数据', value: 26 },
    { name: '财务数据', value: 18 },
    { name: '客户数据', value: 14 },
  ],
  recentAnalyses: [
    { fileName: '2026年7月销售经营数据.xlsx', analyzedAt: '2026-08-02 10:32', status: '已完成' },
    { fileName: '华东区域客户运营数据.csv', analyzedAt: '2026-08-01 16:18', status: '已完成' },
    { fileName: '门店月度目标达成表.xlsx', analyzedAt: '2026-08-01 11:06', status: '处理中' },
    { fileName: '二季度费用明细.csv', analyzedAt: '2026-07-31 17:40', status: '已完成' },
  ],
}
