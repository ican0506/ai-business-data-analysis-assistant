///|
/// Deterministic device-rule result. Python keeps rendering the existing alert schema.
pub(all) struct EquipmentRisk {
  risk_level : String
  triggered_rules : Array[String]
} derive(ToJson)

///|
pub fn evaluate_equipment_risk(
  temperature~ : Double,
  vibration~ : Double,
  fault_count~ : Int,
  status~ : String,
) -> EquipmentRisk {
  let triggered_rules : Array[String] = []
  if fault_count > 0 {
    triggered_rules.push("fault_count")
  }
  if status != "运行" {
    triggered_rules.push("status")
  }
  if temperature >= 80.0 {
    triggered_rules.push("temperature")
  }
  if vibration >= 5.0 {
    triggered_rules.push("vibration")
  }

  let has_high_rule = triggered_rules.contains("fault_count") ||
    triggered_rules.contains("temperature") ||
    triggered_rules.contains("vibration")
  let risk_level = if has_high_rule {
    "高"
  } else if triggered_rules.contains("status") {
    "中"
  } else {
    "正常"
  }
  EquipmentRisk::{ risk_level, triggered_rules }
}
