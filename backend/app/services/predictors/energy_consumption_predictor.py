from datetime import date, datetime
from math import isfinite


class EnergyConsumptionPredictor:
    """Predict unit energy consumption from a moving average plus linear slope."""

    def predict(self, records: list[dict]) -> dict:
        ordered = sorted(records, key=lambda record: self._date_key(record.get("record_date")))
        production_line = next(
            (record.get("production_line") for record in ordered if record.get("production_line")),
            None,
        )
        values = [self._number(record.get("unit_energy_consumption")) for record in ordered]
        values = [value for value in values if value is not None]
        if len(values) < 3:
            return {
                "production_line": production_line,
                "predicted_unit_energy_consumption": None,
                "baseline_unit_energy_consumption": None,
                "deviation_rate": None,
                "trend": "数据不足",
                "warning_level": "数据不足",
            }

        recent_values = values[-3:]
        baseline = sum(recent_values) / len(recent_values)
        slope = self._slope(values)
        predicted = max(0.0, baseline + slope)
        deviation_rate = 0.0 if baseline == 0 else (predicted - baseline) / baseline * 100
        trend = "上升" if slope > 0 else "下降" if slope < 0 else "平稳"
        warning_level = "高风险" if deviation_rate >= 10 else "中风险" if slope > 0 else "正常"
        return {
            "production_line": production_line,
            "predicted_unit_energy_consumption": round(predicted, 2),
            "baseline_unit_energy_consumption": round(baseline, 2),
            "deviation_rate": round(deviation_rate, 2),
            "trend": trend,
            "warning_level": warning_level,
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
