from __future__ import annotations

from collections import defaultdict


class IncidentClassifier:
    def classify(self, anomalies: list[dict]) -> list[dict]:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for anomaly in anomalies:
            grouped[str(anomaly["domain"])].append(anomaly)
        incidents = []
        for domain, rows in grouped.items():
            severity = self._max_severity(rows)
            incidents.append(
                {
                    "incident_type": f"{domain}_risk_incident",
                    "domain": domain,
                    "affected_entities": ",".join(sorted({str(row["entity_id"]) for row in rows})),
                    "severity": severity,
                    "risk_level": self._risk_level(severity),
                    "summary": f"{len(rows)} {domain} anomalies detected",
                    "evidence_json": ";".join(str(row["anomaly_type"]) for row in rows),
                }
            )
        return incidents

    def _max_severity(self, rows: list[dict]) -> str:
        order = {"warning": 1, "severe": 2, "critical": 3}
        return max((str(row["severity"]) for row in rows), key=lambda item: order.get(item, 0), default="warning")

    def _risk_level(self, severity: str) -> str:
        return {"warning": "L1_WATCH", "severe": "L3_FREEZE", "critical": "L5_GLOBAL_HALT"}.get(severity, "L1_WATCH")

