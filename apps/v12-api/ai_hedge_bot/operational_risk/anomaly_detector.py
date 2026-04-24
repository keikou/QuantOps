from __future__ import annotations


class AnomalyDetector:
    def detect(self, metrics: list[dict]) -> list[dict]:
        anomalies = []
        for metric in metrics:
            score = self._score(metric)
            if score < 0.40:
                continue
            anomalies.append(
                {
                    "domain": metric["domain"],
                    "anomaly_type": metric["metric_name"],
                    "entity_id": metric["entity_id"],
                    "observed_value": metric["metric_value"],
                    "expected_value": metric["baseline_value"],
                    "anomaly_score": round(score, 6),
                    "severity": self._severity(score, metric["severity"]),
                    "evidence_json": f"metric={metric['metric_name']};z={metric['z_score']};threshold={metric['threshold_value']}",
                }
            )
        return anomalies

    def _score(self, metric: dict) -> float:
        threshold_score = min(float(metric["metric_value"]) / (float(metric["threshold_value"]) + 0.000001), 1.0)
        z_score = min(abs(float(metric["z_score"])) / 7.0, 1.0)
        breach_bonus = 0.25 if metric["breach"] else 0.0
        return min(0.55 * threshold_score + 0.35 * z_score + breach_bonus, 1.0)

    def _severity(self, score: float, metric_severity: str) -> str:
        if metric_severity == "critical" or score >= 0.80:
            return "critical"
        if score >= 0.60:
            return "severe"
        return "warning"

