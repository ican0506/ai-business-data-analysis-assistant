///|
/// Deterministic order KPIs calculated only from Python-validated order amounts.
/// `None` represents unavailable data; a real 0.0 remains `Some(0.0)`.
pub(all) struct OrderKpi {
  sales_total : Double?
  order_count : Int
  average_order_value : Double?
} derive(ToJson)

///|
pub fn calculate_order_kpis(
  verified_order_amounts : Array[Double],
) -> OrderKpi {
  let order_count = verified_order_amounts.length()
  if verified_order_amounts.length() == 0 {
    return OrderKpi::{
      sales_total: None,
      order_count,
      average_order_value: None,
    }
  }

  let mut total = 0.0
  for amount in verified_order_amounts {
    total = total + amount
  }
  let sales_total = round_currency(total)
  let average = round_currency(total / Double::from_int(verified_order_amounts.length()))
  OrderKpi::{
    sales_total: Some(sales_total),
    order_count,
    average_order_value: Some(average),
  }
}

///|
fn round_currency(value : Double) -> Double {
  (value * 100.0).round() / 100.0
}
