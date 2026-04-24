from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.operational_risk.schemas import TelemetryPoint


class TelemetryLoader:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def load(self) -> list[TelemetryPoint]:
        alpha_reduce_count = self._count_alpha_reductions()
        max_weight_drift = self._max_abs("alpha_dynamic_weights", "weight_delta")
        avg_health_pressure = self._avg("alpha_live_health", "deactivation_pressure")
        return [
            TelemetryPoint("data", "stale_data_seconds", 42.0, 30.0, 180.0, "market_feed", critical=True),
            TelemetryPoint("data", "missing_bar_ratio", 0.01, 0.005, 0.10, "market_feed"),
            TelemetryPoint("execution", "order_reject_rate", 0.02, 0.01, 0.15, "broker"),
            TelemetryPoint("execution", "slippage_bps", 6.0, 5.0, 25.0, "broker"),
            TelemetryPoint("portfolio", "drawdown", 0.018, 0.010, 0.10, "portfolio", critical=True),
            TelemetryPoint("portfolio", "gross_exposure", 0.72, 0.65, 1.25, "portfolio"),
            TelemetryPoint("alpha_system", "alpha_reduction_ratio", min(alpha_reduce_count / 10.0, 1.0), 0.10, 0.50, "alpha_factory"),
            TelemetryPoint("alpha_system", "max_weight_drift", max_weight_drift, 0.02, 0.12, "alpha_factory"),
            TelemetryPoint("alpha_system", "avg_health_pressure", avg_health_pressure, 0.25, 0.70, "alpha_factory"),
            TelemetryPoint("infra", "service_down_count", 0.0, 0.0, 1.0, "runtime", critical=True),
            TelemetryPoint("infra", "db_write_failure_count", 0.0, 0.0, 1.0, "runtime", critical=True),
        ]

    def _count_alpha_reductions(self) -> int:
        row = self.store.fetchone_dict(
            """
            SELECT COUNT(*) AS c
            FROM alpha_retirement_decisions
            WHERE kill_switch_action != 'continue'
            """
        ) or {}
        return int(row.get("c") or 0)

    def _max_abs(self, table: str, column: str) -> float:
        row = self.store.fetchone_dict(f"SELECT MAX(ABS({column})) AS value FROM {table}") or {}
        return float(row.get("value") or 0.0)

    def _avg(self, table: str, column: str) -> float:
        row = self.store.fetchone_dict(f"SELECT AVG({column}) AS value FROM {table}") or {}
        return float(row.get("value") or 0.0)

