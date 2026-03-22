from __future__ import annotations

from typing import Any

CYCLE_STARTED = "cycle_started"
PLANNER_GENERATED = "planner_generated"
ORDER_SUBMITTED = "order_submitted"
ORDER_BLOCKED = "order_blocked"
FILL_RECORDED = "fill_recorded"
PORTFOLIO_UPDATED = "portfolio_updated"
CYCLE_COMPLETED = "cycle_completed"
CYCLE_FAILED = "cycle_failed"


def parse_runtime_event(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": payload.get("event_id"),
        "run_id": payload.get("run_id"),
        "cycle_id": payload.get("cycle_id"),
        "event_type": payload.get("event_type"),
        "reason_code": payload.get("reason_code"),
        "symbol": payload.get("symbol"),
        "mode": payload.get("mode"),
        "source": payload.get("source"),
        "status": payload.get("status"),
        "severity": payload.get("severity"),
        "summary": payload.get("summary"),
        "details": payload.get("details", payload.get("details_json", {})),
        "timestamp": payload.get("timestamp"),
        "created_at": payload.get("created_at"),
    }
