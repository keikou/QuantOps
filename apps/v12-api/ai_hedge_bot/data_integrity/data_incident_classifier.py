from __future__ import annotations


class DataIncidentClassifier:
    def classify(self, anomalies: list[dict]) -> list[dict]:
        incidents = []
        for anomaly in anomalies:
            severity = str(anomaly["severity"])
            risk_level = {"warning": "L1_WATCH", "severe": "L3_FREEZE", "critical": "L5_GLOBAL_HALT"}.get(severity, "L1_WATCH")
            incidents.append(
                {
                    "incident_type": self._incident_type(str(anomaly["anomaly_type"])),
                    "affected_scope": "symbol" if anomaly.get("symbol") else "feed",
                    "affected_entities": str(anomaly.get("symbol") or anomaly.get("feed_id") or ""),
                    "risk_level": risk_level,
                    "recommended_action": self._action(str(anomaly["anomaly_type"]), risk_level),
                    "summary": f"{anomaly['anomaly_type']} detected with {severity} severity",
                    "evidence_json": anomaly.get("evidence_json", ""),
                }
            )
        return incidents

    def _incident_type(self, anomaly_type: str) -> str:
        if anomaly_type in {"stale_feed", "missing_bars"}:
            return "feed_outage"
        if anomaly_type in {"bad_tick", "negative_or_zero_price", "ohlcv_violation"}:
            return "market_data_corruption"
        if anomaly_type == "cross_source_price_deviation":
            return "cross_source_disagreement"
        return "symbol_data_unreliable"

    def _action(self, anomaly_type: str, risk_level: str) -> str:
        if risk_level == "L5_GLOBAL_HALT":
            return "global_data_halt"
        if anomaly_type in {"stale_feed", "missing_bars"}:
            return "freeze_new_exposure"
        return "symbol_partial_halt"

