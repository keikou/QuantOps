from __future__ import annotations

from app.core.deps import get_alert_service


def run_once() -> dict:
    return get_alert_service().evaluate_rules()
