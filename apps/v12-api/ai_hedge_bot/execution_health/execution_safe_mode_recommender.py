from __future__ import annotations


class ExecutionSafeModeRecommender:
    def recommend(self, incidents: list[dict], broker_id: str, venue_id: str) -> dict:
        if not incidents:
            return self._row("global", "execution", "normal_execution", "open_new,increase,reduce,close,cancel", "", "execution_healthy", False)
        max_level = max((str(row["risk_level"]) for row in incidents), key=lambda item: {"L1_WATCH": 1, "L3_FREEZE": 3, "L5_GLOBAL_HALT": 5}.get(item, 0))
        if max_level == "L5_GLOBAL_HALT":
            return self._row("broker", broker_id, "halt_broker", "cancel,reduce_if_lcc_confirms,close_if_lcc_confirms", "open_new,increase", "critical_execution_incident", True)
        if max_level == "L3_FREEZE":
            return self._row("venue", venue_id, "freeze_new_orders", "reduce,close,cancel", "open_new,increase", "execution_freeze_recommended", True)
        return self._row("execution", "system", "watch_execution", "open_new,increase,reduce,close,cancel", "", "execution_watch", False)

    def _row(self, scope: str, target_id: str, mode: str, allowed: str, blocked: str, reason: str, escalate: bool) -> dict:
        return {
            "scope": scope,
            "target_id": target_id,
            "recommended_mode": mode,
            "allowed_order_modes": allowed,
            "blocked_order_modes": blocked,
            "reason": reason,
            "requires_orc_escalation": escalate,
        }

