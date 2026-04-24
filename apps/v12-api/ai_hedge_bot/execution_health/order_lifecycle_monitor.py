from __future__ import annotations

from ai_hedge_bot.execution_health.schemas import ExecutionTelemetry


class OrderLifecycleMonitor:
    def compute(self, telemetry: ExecutionTelemetry) -> dict:
        anomaly_count = telemetry.duplicate_order_count + telemetry.stuck_order_count
        score = max(0.0, 1.0 - anomaly_count / max(telemetry.order_count, 1))
        return {
            "order_lifecycle_score": round(score, 6),
            "duplicate_order_count": telemetry.duplicate_order_count,
            "stuck_order_count": telemetry.stuck_order_count,
            "state_transition_errors": 0,
        }

