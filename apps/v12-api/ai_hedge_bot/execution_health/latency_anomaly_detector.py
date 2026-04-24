from __future__ import annotations

from ai_hedge_bot.execution_health.schemas import ExecutionTelemetry


class LatencyAnomalyDetector:
    def detect(self, telemetry: ExecutionTelemetry) -> list[dict]:
        observed = max(telemetry.api_latency_ms, telemetry.venue_latency_ms)
        z_score = (observed - 100.0) / 100.0
        if z_score < 3.0:
            return []
        severity = "critical" if z_score >= 7.0 else "severe" if z_score >= 5.0 else "warning"
        return [
            {
                "broker_id": telemetry.broker_id,
                "venue_id": telemetry.venue_id,
                "order_id": "",
                "anomaly_type": "execution_latency_spike",
                "observed_value": observed,
                "expected_value": 100.0,
                "anomaly_score": min(abs(z_score) / 7.0, 1.0),
                "severity": severity,
                "evidence_json": f"latency_ms={observed};z={z_score}",
            }
        ]

