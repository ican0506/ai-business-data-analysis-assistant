from datetime import date, datetime
from math import isfinite


class ProductionCompletionPredictor:
    """Forecast next-period cement output and evaluate a supplied target date."""

    def predict(self, records: list[dict], target_date: date | None = None) -> dict:
        ordered = sorted(records, key=lambda record: self._date_key(record.get("record_date")))
        production_line = next(
            (record.get("production_line") for record in ordered if record.get("production_line")),
            None,
        )
        valid = [
            record
            for record in ordered
            if self._number(record.get("cement_output")) is not None
            and self._number(record.get("planned_output")) is not None
        ]
        if not valid:
            return {
                "production_line": production_line,
                "completion_rate": None,
                "predicted_output": None,
                "trend": "数据不足",
                "delay_risk": None,
            }

        cement_outputs = [self._number(record["cement_output"]) for record in valid]
        planned_outputs = [self._number(record["planned_output"]) for record in valid]
        actual_total = sum(cement_outputs)
        planned_total = sum(planned_outputs)
        completion_rate = None if planned_total == 0 else round(actual_total / planned_total * 100, 2)
        if len(cement_outputs) >= 3:
            recent = cement_outputs[-3:]
            slope = self._slope(cement_outputs)
            predicted_output = max(0.0, sum(recent) / len(recent) + slope)
            trend = "上升" if slope > 0 else "下降" if slope < 0 else "平稳"
        else:
            predicted_output = cement_outputs[-1]
            trend = "数据不足"

        delay_risk = None
        if target_date is not None:
            days_remaining = max(0, (target_date - self._date_key(valid[-1].get("record_date"))).days)
            projected_total = actual_total + predicted_output * days_remaining
            delay_risk = "可能延期" if projected_total < planned_total else "无延期风险"
        return {
            "production_line": production_line,
            "completion_rate": completion_rate,
            "predicted_output": round(predicted_output, 2),
            "trend": trend,
            "delay_risk": delay_risk,
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
