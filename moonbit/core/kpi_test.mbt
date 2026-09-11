test "order KPI sums verified order amounts and calculates average order value" {
  let result = calculate_order_kpis([120.0, 80.0, 0.0])
  @test.assert_eq(result.sales_total, Some(200.0))
  @test.assert_eq(result.order_count, 3)
  @test.assert_eq(result.average_order_value, Some(66.67))
}

test "order KPI keeps an empty verified amount list unavailable instead of zero" {
  let result = calculate_order_kpis([])
  @test.assert_eq(result.sales_total, None)
  @test.assert_eq(result.order_count, 0)
  @test.assert_eq(result.average_order_value, None)
}
