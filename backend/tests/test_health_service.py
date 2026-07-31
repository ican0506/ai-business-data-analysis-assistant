from app.services.health_service import build_health_payload


def test_build_health_payload_marks_database_unavailable_when_probe_fails():
    payload = build_health_payload(lambda: False)

    assert payload == {"status": "degraded", "database": "unavailable"}
