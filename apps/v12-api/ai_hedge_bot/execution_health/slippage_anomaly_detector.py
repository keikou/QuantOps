from __future__ import annotations

from ai_hedge_bot.execution_health.schemas import ExecutionTelemetry


class SlippageAnomalyDetector:
    def detect(self, telemetry: ExecutionTelemetry) -> list[dict]:
        z_score = (telemetry.realized_slippage_bps - 5.0) / 5.0
        if z_score < 3.0 and telemetry.realized_slippage_bps < 25.0:
            return []
        severity = "critical" if z_score >= 7.0 else "severe" if z_score >= 5.0 else "warning"
        return [
            {
                "broker_id": telemetry.broker_id,
                "venue_id": telemetry.venue_id,
                "order_id": "",
                "anomaly_type": "slippage_spike",
                "observed_value": telemetry.realized_slippage_bps,
                "expected_value": 5.0,
                "anomaly_score": min(abs(z_score) / 7.0, 1.0),
                "severity": severity,
                "evidence_json": f"slippage_bps={telemetry.realized_slippage_bps};z={z_score}",
            }
        ]

