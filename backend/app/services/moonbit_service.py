"""Safe subprocess boundary for the repository's MoonBit deterministic core."""

from __future__ import annotations

import json
import logging
import math
import subprocess
from typing import Any

from app.core.config import Settings, get_settings


logger = logging.getLogger(__name__)


class MoonBitService:
    """Invoke one JSON-in/JSON-out MoonBit executable without leaking failures upstream."""

    _RISK_LEVELS = {"高", "中", "正常"}
    _RISK_RULES = {"fault_count", "status", "temperature", "vibration"}
    _INVALID = object()

    def __init__(self, settings: Settings | Any | None = None) -> None:
        self._settings = settings or get_settings()

    def calculate_order_kpis(
        self,
        verified_order_amounts: list[float],
    ) -> dict[str, float | int | None] | None:
        result = self._invoke(
            {
                "operation": "order_kpi",
                "verified_order_amounts": verified_order_amounts,
            }
        )
        return self._validate_order_kpis(
            result,
            expected_order_count=len(verified_order_amounts),
        )

    def evaluate_equipment_risk(
        self,
        *,
        temperature: float,
        vibration: float,
        fault_count: int,
        status: str,
    ) -> dict[str, object] | None:
        result = self._invoke(
            {
                "operation": "equipment_risk",
                "temperature": temperature,
                "vibration": vibration,
                "fault_count": fault_count,
                "status": status,
            }
        )
        return self._validate_equipment_risk(result)

    def _invoke(self, payload: dict[str, object]) -> object | None:
        if not self._settings.moonbit_engine_enabled:
            return None
        path = str(self._settings.moonbit_engine_path).strip()
        if not path:
            logger.warning("MoonBit Core Engine is enabled but no executable path is configured")
            return None
        try:
            completed = subprocess.run(
                [path],
                input=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=float(self._settings.moonbit_engine_timeout_seconds),
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            logger.warning("MoonBit Core Engine unavailable; using Python fallback: %s", type(exc).__name__)
            return None
        if completed.returncode != 0:
            logger.warning("MoonBit Core Engine exited with code %s; using Python fallback", completed.returncode)
            return None
        try:
            return json.loads(completed.stdout)
        except (TypeError, json.JSONDecodeError):
            logger.warning("MoonBit Core Engine returned invalid JSON; using Python fallback")
            return None

    @classmethod
    def _validate_order_kpis(
        cls,
        result: object | None,
        *,
        expected_order_count: int,
    ) -> dict[str, float | int | None] | None:
        if not isinstance(result, dict):
            return None
        sales_total = cls._number_or_none(result.get("sales_total"))
        average = cls._number_or_none(result.get("average_order_value"))
        order_count = result.get("order_count")
        if sales_total is cls._INVALID or average is cls._INVALID:
            return None
        if (
            not isinstance(order_count, int)
            or isinstance(order_count, bool)
            or order_count < 0
            or order_count != expected_order_count
        ):
            return None
        if order_count == 0 and (sales_total is not None or average is not None):
            return None
        if order_count > 0 and (sales_total is None or average is None):
            return None
        return {"sales_total": sales_total, "order_count": order_count, "average_order_value": average}

    @classmethod
    def _validate_equipment_risk(cls, result: object | None) -> dict[str, object] | None:
        if not isinstance(result, dict):
            return None
        risk_level = result.get("risk_level")
        triggered_rules = result.get("triggered_rules")
        if risk_level not in cls._RISK_LEVELS or not isinstance(triggered_rules, list):
            return None
        if (
            any(not isinstance(rule, str) or rule not in cls._RISK_RULES for rule in triggered_rules)
            or len(triggered_rules) != len(set(triggered_rules))
        ):
            return None
        return {"risk_level": risk_level, "triggered_rules": triggered_rules}

    @classmethod
    def _number_or_none(cls, value: object) -> float | None | object:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return cls._INVALID
        numeric = float(value)
        return numeric if math.isfinite(numeric) else cls._INVALID
