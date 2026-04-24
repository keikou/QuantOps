from __future__ import annotations


class DataSafeModeRecommender:
    def recommend(self, incidents: list[dict]) -> dict:
        if not incidents:
            return self._row("global", "data", "normal_data", "open_new,increase,reduce,close,cancel", "", "data_healthy", False)
        max_level = max((str(row["risk_level"]) for row in incidents), key=lambda item: {"L1_WATCH": 1, "L3_FREEZE": 3, "L5_GLOBAL_HALT": 5}.get(item, 0))
        target = str(incidents[0].get("affected_entities") or "data")
        if max_level == "L5_GLOBAL_HALT":
            return self._row("global", "data", "global_data_halt", "cancel,reduce_if_lcc_confirms,close_if_lcc_confirms", "open_new,increase", "critical_data_incident", True)
        if max_level == "L3_FREEZE":
            return self._row("symbol", target, "freeze_new_exposure", "reduce,close,cancel", "open_new,increase", "data_freeze_recommended", True)
        return self._row("data", "system", "watch_data", "open_new,increase,reduce,close,cancel", "", "data_watch", False)

    def _row(self, scope: str, target_id: str, mode: str, allowed: str, blocked: str, reason: str, escalate: bool) -> dict:
        return {
            "scope": scope,
            "target_id": target_id,
            "recommended_mode": mode,
            "reason": reason,
            "allowed_order_modes": allowed,
            "blocked_order_modes": blocked,
            "requires_orc_escalation": escalate,
        }

