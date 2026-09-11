test "equipment risk marks temperature vibration and fault breaches as high risk" {
  let result = evaluate_equipment_risk(
    temperature=85.0,
    vibration=5.2,
    fault_count=1,
    status="运行",
  )
  @test.assert_eq(result.risk_level, "高")
  @test.assert_eq(result.triggered_rules.length(), 3)
}

test "equipment risk treats a stopped device as medium risk when no high threshold is breached" {
  let result = evaluate_equipment_risk(
    temperature=65.0,
    vibration=3.0,
    fault_count=0,
    status="停机",
  )
  @test.assert_eq(result.risk_level, "中")
  @test.assert_eq(result.triggered_rules.length(), 1)
}
