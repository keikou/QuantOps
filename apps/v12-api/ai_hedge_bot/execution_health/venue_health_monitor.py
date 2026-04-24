from __future__ import annotations

from ai_hedge_bot.execution_health.schemas import ExecutionTelemetry


class VenueHealthMonitor:
    def compute(self, telemetry: ExecutionTelemetry) -> dict:
        fill_rate = telemetry.fill_count / max(telemetry.order_count, 1)
        partial_fill_rate = telemetry.partial_fill_count / max(telemetry.order_count, 1)
        reject_rate = telemetry.reject_count / max(telemetry.order_count, 1)
        fill_quality = max(0.0, min(1.0, fill_rate))
        slippage_score = max(0.0, 1.0 - telemetry.realized_slippage_bps / 50.0)
        latency_score = max(0.0, 1.0 - telemetry.venue_latency_ms / 1000.0)
        reject_score = max(0.0, 1.0 - reject_rate / 0.30)
        partial_score = max(0.0, 1.0 - partial_fill_rate / 0.50)
        score = 0.30 * fill_quality + 0.25 * slippage_score + 0.20 * latency_score + 0.15 * reject_score + 0.10 * partial_score
        return {
            "venue_id": telemetry.venue_id,
            "fill_rate": round(fill_rate, 6),
            "realized_slippage_bps": telemetry.realized_slippage_bps,
            "latency_ms": telemetry.venue_latency_ms,
            "reject_rate": round(reject_rate, 6),
            "partial_fill_rate": round(partial_fill_rate, 6),
            "venue_health_score": round(score, 6),
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

