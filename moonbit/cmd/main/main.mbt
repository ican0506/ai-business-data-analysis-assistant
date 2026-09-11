///|
/// JSON stdin/stdout adapter. The `core` package holds all business rules.
struct EngineRequest {
  operation : String
  verified_order_amounts : Array[Double]?
  temperature : Double?
  vibration : Double?
  fault_count : Int?
  status : String?
} derive(FromJson)

fn error_response(message : String) -> Json {
  { "error": message }
}

fn run_request(request : EngineRequest) -> Json {
  match request.operation {
    "order_kpi" => {
      let amounts = match request.verified_order_amounts {
        Some(values) => values
        None => []
      }
      @core.calculate_order_kpis(amounts).to_json()
    }
    "equipment_risk" => {
      let temperature = match request.temperature {
        Some(value) => value
        None => return error_response("temperature is required")
      }
      let vibration = match request.vibration {
        Some(value) => value
        None => return error_response("vibration is required")
      }
      let fault_count = match request.fault_count {
        Some(value) => value
        None => return error_response("fault_count is required")
      }
      let status = match request.status {
        Some(value) => value
        None => return error_response("status is required")
      }
      @core.evaluate_equipment_risk(
        temperature~,
        vibration~,
        fault_count~,
        status~,
      ).to_json()
    }
    _ => error_response("unsupported operation")
  }
}

async fn main {
  let input = @stdio.stdin.read_all().text()
  let response : Json = try {
    let request : EngineRequest = @json.from_json(@json.parse(input))
    run_request(request)
  } catch {
    _ => error_response("invalid request")
  }
  @stdio.stdout.write(response.stringify() + "\n")
}
