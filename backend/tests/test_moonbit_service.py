from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

from app.services.moonbit_service import MoonBitService


def enabled_settings() -> SimpleNamespace:
    return SimpleNamespace(
        moonbit_engine_enabled=True,
        moonbit_engine_path="C:/tools/moonbit-core.exe",
        moonbit_engine_timeout_seconds=0.5,
    )


def test_order_kpi_serializes_verified_amounts_and_returns_strictly_validated_result(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["payload"] = json.loads(kwargs["input"])
        observed["encoding"] = kwargs["encoding"]
        observed["timeout"] = kwargs["timeout"]
        return subprocess.CompletedProcess(
            command,
            0,
            stdout='{"sales_total":200.0,"order_count":3,"average_order_value":66.67}',
            stderr="",
        )

    monkeypatch.setattr("app.services.moonbit_service.subprocess.run", fake_run)

    result = MoonBitService(settings=enabled_settings()).calculate_order_kpis([120.0, 80.0, 0.0])

    assert observed["command"] == ["C:/tools/moonbit-core.exe"]
    assert observed["payload"] == {
        "operation": "order_kpi",
        "verified_order_amounts": [120.0, 80.0, 0.0],
    }
    assert observed["encoding"] == "utf-8"
    assert observed["timeout"] == 0.5
    assert result == {"sales_total": 200.0, "order_count": 3, "average_order_value": 66.67}


def test_order_kpi_rejects_invalid_moonbit_json_and_returns_python_fallback_signal(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.moonbit_service.subprocess.run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            command,
            0,
            stdout='{"sales_total":"200","order_count":3}',
            stderr="",
        ),
    )

    assert MoonBitService(settings=enabled_settings()).calculate_order_kpis([200.0]) is None


def test_equipment_risk_uses_moonbit_rule_result_without_reimplementing_thresholds(monkeypatch) -> None:
    def fake_run(command, **kwargs):
        assert json.loads(kwargs["input"]) == {
            "operation": "equipment_risk",
            "temperature": 85.0,
            "vibration": 5.2,
            "fault_count": 1,
            "status": "运行",
        }
        return subprocess.CompletedProcess(
            command,
            0,
            stdout='{"risk_level":"高","triggered_rules":["fault_count","temperature","vibration"]}',
            stderr="",
        )

    monkeypatch.setattr("app.services.moonbit_service.subprocess.run", fake_run)

    result = MoonBitService(settings=enabled_settings()).evaluate_equipment_risk(
        temperature=85.0,
        vibration=5.2,
        fault_count=1,
        status="运行",
    )

    assert result == {
        "risk_level": "高",
        "triggered_rules": ["fault_count", "temperature", "vibration"],
    }


def test_timeout_or_disabled_engine_returns_none_for_existing_python_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.moonbit_service.subprocess.run",
        lambda *args, **kwargs: (_ for _ in ()).throw(subprocess.TimeoutExpired("moonbit", 0.5)),
    )

    assert MoonBitService(settings=enabled_settings()).calculate_order_kpis([100.0]) is None
    disabled = SimpleNamespace(
        moonbit_engine_enabled=False,
        moonbit_engine_path="C:/tools/moonbit-core.exe",
        moonbit_engine_timeout_seconds=0.5,
    )
    assert MoonBitService(settings=disabled).calculate_order_kpis([100.0]) is None


def test_order_kpi_invokes_the_real_moonbit_native_executable() -> None:
    executable = (
        Path(__file__).resolve().parents[2]
        / "moonbit"
        / "_build"
        / "native"
        / "release"
        / "build"
        / "cmd"
        / "main"
        / "main.exe"
    )
    if not executable.is_file():
        import pytest

        pytest.skip("MoonBit native executable has not been built")

    settings = SimpleNamespace(
        moonbit_engine_enabled=True,
        moonbit_engine_path=str(executable),
        moonbit_engine_timeout_seconds=2.0,
    )

    assert MoonBitService(settings=settings).calculate_order_kpis([1200.0, 800.0, 0.0]) == {
        "sales_total": 2000.0,
        "order_count": 3,
        "average_order_value": 666.67,
    }


def test_equipment_risk_invokes_the_real_moonbit_native_executable() -> None:
    executable = (
        Path(__file__).resolve().parents[2]
        / "moonbit"
        / "_build"
        / "native"
        / "release"
        / "build"
        / "cmd"
        / "main"
        / "main.exe"
    )
    if not executable.is_file():
        import pytest

        pytest.skip("MoonBit native executable has not been built")

    settings = SimpleNamespace(
        moonbit_engine_enabled=True,
        moonbit_engine_path=str(executable),
        moonbit_engine_timeout_seconds=2.0,
    )

    assert MoonBitService(settings=settings).evaluate_equipment_risk(
        temperature=85.0,
        vibration=3.0,
        fault_count=0,
        status="运行",
    ) == {
        "risk_level": "高",
        "triggered_rules": ["temperature"],
    }
