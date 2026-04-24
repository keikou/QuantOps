from __future__ import annotations

from ai_hedge_bot.execution_health.schemas import ExecutionTelemetry


class BrokerHealthMonitor:
    def compute(self, telemetry: ExecutionTelemetry) -> dict:
        reject_rate = telemetry.reject_count / max(telemetry.order_count, 1)
        cancel_success_rate = telemetry.cancel_success_count / telemetry.cancel_count if telemetry.cancel_count else 1.0
        replace_success_rate = telemetry.replace_success_count / telemetry.replace_count if telemetry.replace_count else 1.0
        heartbeat_score = 1.0 if telemetry.heartbeat_ok else 0.0
        latency_score = max(0.0, 1.0 - telemetry.api_latency_ms / 1000.0)
        reject_score = max(0.0, 1.0 - reject_rate / 0.30)
        cancel_replace_score = (cancel_success_rate + replace_success_rate) / 2.0
        sync_score = (float(telemetry.position_sync_ok) + float(telemetry.open_order_sync_ok)) / 2.0
        score = (
            0.25 * heartbeat_score
            + 0.20 * latency_score
            + 0.20 * reject_score
            + 0.15 * cancel_replace_score
            + 0.20 * sync_score
        )
        return {
            "broker_id": telemetry.broker_id,
            "heartbeat_ok": telemetry.heartbeat_ok,
            "api_latency_ms": telemetry.api_latency_ms,
            "reject_rate": round(reject_rate, 6),
            "cancel_success_rate": round(cancel_success_rate, 6),
            "replace_success_rate": round(replace_success_rate, 6),
            "position_sync_ok": telemetry.position_sync_ok,
            "open_order_sync_ok": telemetry.open_order_sync_ok,
            "broker_health_score": round(score, 6),
            "health_state": self._state(score),
        }

    def _state(self, score: float) -> str:
        if score < 0.35:
            return "critical"
        if score < 0.55:
            return "degraded"
        if score < 0.75:
            return "watch"
        return "healthy"
