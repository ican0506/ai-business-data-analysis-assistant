from collections.abc import Callable


def build_health_payload(database_probe: Callable[[], bool]) -> dict[str, str]:
    database_ok = database_probe()
    return {
        "status": "ok" if database_ok else "degraded",
        "database": "available" if database_ok else "unavailable",
    }
