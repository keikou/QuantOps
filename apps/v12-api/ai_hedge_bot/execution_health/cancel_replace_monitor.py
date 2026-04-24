from __future__ import annotations

from ai_hedge_bot.execution_health.schemas import ExecutionTelemetry


class CancelReplaceMonitor:
    def detect(self, telemetry: ExecutionTelemetry) -> list[dict]:
        anomalies = []
        cancel_success_rate = telemetry.cancel_success_count / telemetry.cancel_count if telemetry.cancel_count else 1.0
        replace_success_rate = telemetry.replace_success_count / telemetry.replace_count if telemetry.replace_count else 1.0
        if telemetry.cancel_count and cancel_success_rate < 0.90:
            anomalies.append(self._row(telemetry, "cancel_failure", cancel_success_rate, 0.90))
        if telemetry.replace_count and replace_success_rate < 0.90:
            anomalies.append(self._row(telemetry, "replace_failure", replace_success_rate, 0.90))
        return anomalies

    def _row(self, telemetry: ExecutionTelemetry, anomaly_type: str, observed: float, expected: float) -> dict:
        severity = "critical" if observed < 0.70 else "severe"
        return {
            "broker_id": telemetry.broker_id,
            "venue_id": telemetry.venue_id,
            "order_id": "",
            "anomaly_type": anomaly_type,
            "observed_value": observed,
            "expected_value": expected,
            "anomaly_score": min((expected - observed) / expected, 1.0),
            "severity": severity,
            "evidence_json": f"{anomaly_type}_rate={observed}",
        }
