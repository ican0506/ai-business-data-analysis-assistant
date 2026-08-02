import { describe, expect, it } from 'vitest'

import router from './index'

describe('后台导航路由', () => {
  it('提供四个受保护的业务页面路由', () => {
    const routeNames = router.getRoutes().map((route) => route.name)

    expect(routeNames).toEqual(expect.arrayContaining([
      'dashboard',
      'datasets',
      'ai-analysis',
      'downloads',
    ]))
  })
})
