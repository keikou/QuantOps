from __future__ import annotations

from typing import Any

RISK_GUARD_BLOCK = "risk_guard_block"
STALE_MARKET_DATA = "stale_market_data"
MISSING_PRICE = "missing_price"
EXECUTION_DISABLED = "execution_disabled"
NO_POSITION_DELTA = "no_position_delta"
ORDER_REJECTED = "order_rejected"
DEGRADED_MODE = "degraded_mode"
SCHEDULER_OVERLAP = "scheduler_overlap"
TIMEOUT_GUARD = "timeout_guard"
STARTUP_GUARD_FAILURE = "startup_guard_failure"

REASON_SEVERITY: dict[str, str] = {
    RISK_GUARD_BLOCK: "high",
    STALE_MARKET_DATA: "high",
    MISSING_PRICE: "high",
    EXECUTION_DISABLED: "critical",
    NO_POSITION_DELTA: "info",
    ORDER_REJECTED: "high",
    DEGRADED_MODE: "medium",
    SCHEDULER_OVERLAP: "high",
    TIMEOUT_GUARD: "high",
    STARTUP_GUARD_FAILURE: "critical",
}

REASON_SUMMARY: dict[str, str] = {
    RISK_GUARD_BLOCK: "Risk guard prevented order submission.",
    STALE_MARKET_DATA: "Market data is stale for the requested action.",
    MISSING_PRICE: "Required pricing data is missing.",
    EXECUTION_DISABLED: "Execution is disabled by runtime control state.",
    NO_POSITION_DELTA: "No actionable portfolio delta remains.",
    ORDER_REJECTED: "Order could not be accepted.",
    DEGRADED_MODE: "Runtime is operating in degraded mode.",
    SCHEDULER_OVERLAP: "Scheduler overlap prevented this cycle.",
    TIMEOUT_GUARD: "A timeout guard interrupted execution.",
    STARTUP_GUARD_FAILURE: "Startup guard prevented runtime activation.",
}


def build_reason(
    code: str,
    *,
    summary: str | None = None,
    detail: dict[str, Any] | None = None,
    severity: str | None = None,
) -> dict[str, Any]:
    resolved_code = str(code or "").strip() or ORDER_REJECTED
    return {
        "code": resolved_code,
        "severity": severity or REASON_SEVERITY.get(resolved_code, "medium"),
        "message": summary or REASON_SUMMARY.get(resolved_code, resolved_code.replace("_", " ")),
        "details": detail or {},
    }
