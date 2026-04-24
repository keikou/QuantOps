from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionTelemetry:
    broker_id: str
    venue_id: str
    order_count: int
    fill_count: int
    reject_count: int
    cancel_count: int
    cancel_success_count: int
    replace_count: int
    replace_success_count: int
    heartbeat_ok: bool
    position_sync_ok: bool
    open_order_sync_ok: bool
    api_latency_ms: float
    venue_latency_ms: float
    realized_slippage_bps: float
    partial_fill_count: int
    duplicate_order_count: int
    stuck_order_count: int

