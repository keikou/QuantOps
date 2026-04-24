from __future__ import annotations

from ai_hedge_bot.execution_health.schemas import ExecutionTelemetry


class FillQualityEngine:
    def compute(self, telemetry: ExecutionTelemetry) -> dict:
        fill_rate = telemetry.fill_count / max(telemetry.order_count, 1)
        partial_fill_rate = telemetry.partial_fill_count / max(telemetry.order_count, 1)
        fill_quality_score = max(0.0, min(1.0, fill_rate * (1.0 - min(partial_fill_rate, 0.5))))
        return {
            "fill_quality_score": round(fill_quality_score, 6),
            "realized_slippage_bps": telemetry.realized_slippage_bps,
            "partial_fill_rate": round(partial_fill_rate, 6),
        }

