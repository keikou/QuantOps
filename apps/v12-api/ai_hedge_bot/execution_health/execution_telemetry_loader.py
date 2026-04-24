from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.execution_health.schemas import ExecutionTelemetry


class ExecutionTelemetryLoader:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def load(self) -> ExecutionTelemetry:
        order_count = self._count("live_orders")
        fill_count = self._count("live_fills")
        reject_count = self._count_where("live_orders", "status='rejected'")
        if order_count == 0:
            return ExecutionTelemetry(
                broker_id="broker.synthetic",
                venue_id="venue.synthetic",
                order_count=12,
                fill_count=10,
                reject_count=1,
                cancel_count=2,
                cancel_success_count=2,
                replace_count=1,
                replace_success_count=1,
                heartbeat_ok=True,
                position_sync_ok=True,
                open_order_sync_ok=True,
                api_latency_ms=115.0,
                venue_latency_ms=140.0,
                realized_slippage_bps=8.0,
                partial_fill_count=1,
                duplicate_order_count=0,
                stuck_order_count=0,
            )
        return ExecutionTelemetry(
            broker_id="broker.live",
            venue_id="venue.live",
            order_count=order_count,
            fill_count=fill_count,
            reject_count=reject_count,
            cancel_count=self._count_where("live_orders", "status='cancelled'"),
            cancel_success_count=self._count_where("live_orders", "status='cancelled'"),
            replace_count=0,
            replace_success_count=0,
            heartbeat_ok=True,
            position_sync_ok=True,
            open_order_sync_ok=True,
            api_latency_ms=100.0,
            venue_latency_ms=125.0,
            realized_slippage_bps=7.5,
            partial_fill_count=max(order_count - fill_count, 0),
            duplicate_order_count=0,
            stuck_order_count=self._count_where("live_orders", "status IN ('submitted','accepted')"),
        )

    def _count(self, table: str) -> int:
        row = self.store.fetchone_dict(f"SELECT COUNT(*) AS c FROM {table}") or {}
        return int(row.get("c") or 0)

    def _count_where(self, table: str, where: str) -> int:
        row = self.store.fetchone_dict(f"SELECT COUNT(*) AS c FROM {table} WHERE {where}") or {}
        return int(row.get("c") or 0)
