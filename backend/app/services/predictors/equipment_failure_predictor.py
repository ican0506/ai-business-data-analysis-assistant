from datetime import date, datetime
from math import isfinite


class EquipmentFailurePredictor:
    """Forecast the next equipment condition point using simple historical slopes."""

    def predict(self, records: list[dict]) -> dict:
        ordered = sorted(records, key=lambda record: self._date_key(record.get("record_date")))
        equipment_name = next(
            (record.get("equipment_name") for record in ordered if record.get("equipment_name")),
            None,
        )
        valid = [
            record
            for record in ordered
            if self._number(record.get("temperature")) is not None
            and self._number(record.get("vibration")) is not None
        ]
        if len(valid) < 3:
            return {
                "equipment_name": equipment_name,
                "predicted_temperature": None,
                "predicted_vibration": None,
                "risk_level": "数据不足",
                "reasons": ["有效温度和振动历史记录少于 3 条，无法进行确定性趋势预测。"],
                "maintenance_suggestion": "补充至少 3 条有效设备运行记录后再评估维护时间。",
            }

        temperatures = [self._number(record["temperature"]) for record in valid]
        vibrations = [self._number(record["vibration"]) for record in valid]
        temperature_slope = self._slope(temperatures)
        vibration_slope = self._slope(vibrations)
        predicted_temperature = round(temperatures[-1] + temperature_slope, 2)
        predicted_vibration = round(vibrations[-1] + vibration_slope, 3)
        score = 0
        reasons: list[str] = []

        if predicted_temperature >= 80:
            score += 2
            reasons.append(f"预测温度 {predicted_temperature} 已达到 80℃ 异常阈值。")
        elif temperature_slope > 0:
            score += 1
            reasons.append("温度呈持续上升趋势。")
        if predicted_vibration >= 5:
            score += 2
            reasons.append(f"预测振动值 {predicted_vibration} 已达到 5.0 异常阈值。")
        elif vibration_slope > 0:
            score += 1
            reasons.append("振动呈持续上升趋势。")
        if any((self._number(record.get("fault_count")) or 0) > 0 for record in valid):
            score += 2
            reasons.append("历史记录中存在故障次数大于 0 的情况。")
        if any(record.get("status") and record.get("status") != "运行" for record in valid):
            score += 2
            reasons.append("历史记录中存在非“运行”状态。")

        risk_level = "高风险" if score >= 3 else "中风险" if score >= 1 else "正常"
        suggestion = {
            "高风险": "建议在 24 小时内安排现场检查和预防性维护。",
            "中风险": "建议在 3 个工作日内安排重点点检和维护评估。",
            "正常": "建议按既定计划持续进行例行点检。",
        }[risk_level]
        if not reasons:
            reasons.append("预测温度、振动和历史运行状态未触发风险规则。")
        return {
            "equipment_name": equipment_name,
            "predicted_temperature": predicted_temperature,
            "predicted_vibration": predicted_vibration,
            "risk_level": risk_level,
            "reasons": reasons,
            "maintenance_suggestion": suggestion,
        }

    @staticmethod
    def _number(value: object) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if isfinite(number) else None

    @staticmethod
    def _slope(values: list[float]) -> float:
        return (values[-1] - values[0]) / (len(values) - 1)

    @staticmethod
    def _date_key(value: object) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value)
        return date.min
