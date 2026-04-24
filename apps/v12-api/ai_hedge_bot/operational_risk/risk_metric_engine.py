from __future__ import annotations

from ai_hedge_bot.operational_risk.schemas import TelemetryPoint


class RiskMetricEngine:
    def compute(self, telemetry: list[TelemetryPoint]) -> list[dict]:
        rows = []
        for point in telemetry:
            z_score = (point.metric_value - point.baseline_value) / (abs(point.baseline_value) + 0.01)
            breach = point.metric_value >= point.threshold_value
            severity = self._severity(point.metric_value, point.threshold_value, z_score, point.critical)
            rows.append(
                {
                    "metric_name": point.metric_name,
                    "domain": point.domain,
                    "metric_value": round(point.metric_value, 6),
                    "baseline_value": round(point.baseline_value, 6),
                    "z_score": round(z_score, 6),
                    "threshold_value": round(point.threshold_value, 6),
                    "breach": breach,
                    "severity": severity,
                    "entity_id": point.entity_id,
                    "critical": point.critical,
                }
            )
        return rows

    def _severity(self, value: float, threshold: float, z_score: float, critical: bool) -> str:
        if critical and value >= threshold:
            return "critical"
        ratio = value / (threshold + 0.000001)
        if ratio >= 1.0 or abs(z_score) >= 7.0:
            return "critical"
        if ratio >= 0.75 or abs(z_score) >= 5.0:
            return "severe"
        if ratio >= 0.50 or abs(z_score) >= 3.0:
            return "warning"
        return "normal"

