from __future__ import annotations

from typing import Any

from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id

CYCLE_STARTED = "cycle_started"
PLANNER_GENERATED = "planner_generated"
ORDER_SUBMITTED = "order_submitted"
ORDER_BLOCKED = "order_blocked"
FILL_RECORDED = "fill_recorded"
PORTFOLIO_UPDATED = "portfolio_updated"
CYCLE_COMPLETED = "cycle_completed"
CYCLE_FAILED = "cycle_failed"


def build_runtime_event(
    *,
    event_type: str,
    run_id: str | None,
    cycle_id: str | None,
    mode: str | None,
    source: str,
    severity: str = "info",
    status: str = "ok",
    summary: str = "",
    reason_code: str | None = None,
    symbol: str | None = None,
    timestamp: str | None = None,
    details: dict[str, Any] | None = None,
    event_id: str | None = None,
) -> dict[str, Any]:
    as_of = timestamp or utc_now_iso()
    return {
        "event_id": event_id or new_cycle_id(),
        "run_id": run_id,
        "cycle_id": cycle_id,
        "event_type": str(event_type or "").strip(),
        "reason_code": str(reason_code or "").strip() or None,
        "symbol": str(symbol or "").strip() or None,
        "mode": str(mode or "").strip() or None,
        "source": str(source or "").strip() or "runtime",
        "status": str(status or "").strip() or "ok",
        "severity": str(severity or "").strip() or "info",
        "summary": str(summary or "").strip(),
        "details_json": details or {},
        "timestamp": as_of,
        "created_at": as_of,
    }
