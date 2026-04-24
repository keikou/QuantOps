from __future__ import annotations


class ExecutionIncidentClassifier:
    def classify(self, anomalies: list[dict]) -> list[dict]:
        incidents = []
        for anomaly in anomalies:
            severity = str(anomaly["severity"])
            risk_level = {"warning": "L1_WATCH", "severe": "L3_FREEZE", "critical": "L5_GLOBAL_HALT"}.get(severity, "L1_WATCH")
            incidents.append(
                {
                    "incident_type": anomaly["anomaly_type"],
                    "broker_id": anomaly.get("broker_id"),
                    "venue_id": anomaly.get("venue_id"),
                    "affected_orders": anomaly.get("order_id", ""),
                    "risk_level": risk_level,
                    "recommended_action": self._action(str(anomaly["anomaly_type"]), risk_level),
                    "summary": f"{anomaly['anomaly_type']} detected with {severity} severity",
                    "evidence_json": anomaly.get("evidence_json", ""),
                }
            )
        return incidents

    def _action(self, anomaly_type: str, risk_level: str) -> str:
        if anomaly_type in {"duplicate_order", "position_sync_mismatch"}:
            return "global_execution_halt"
        if risk_level == "L3_FREEZE":
            return "freeze_new_orders"
        if risk_level == "L5_GLOBAL_HALT":
            return "halt_broker"
        return "watch_execution"

