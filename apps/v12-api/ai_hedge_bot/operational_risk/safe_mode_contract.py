from __future__ import annotations


class SafeModeContract:
    def build(self, risk_level: str, scope: str, reason: str, event_id: str = "") -> dict:
        allowed, blocked = self._permissions(risk_level)
        return {
            "risk_state": risk_level,
            "scope": scope,
            "allowed_order_modes": ",".join(allowed),
            "blocked_order_modes": ",".join(blocked),
            "reason": reason,
            "event_id": event_id,
        }

    def _permissions(self, risk_level: str) -> tuple[list[str], list[str]]:
        if risk_level in {"L0_NORMAL", "L1_WATCH"}:
            return ["open_new", "increase", "reduce", "close", "cancel"], []
        if risk_level == "L2_REDUCE":
            return ["limited_open_new", "limited_increase", "reduce", "close", "cancel"], ["high_risk_open_new"]
        if risk_level == "L3_FREEZE":
            return ["reduce", "close", "cancel"], ["open_new", "increase"]
        if risk_level == "L4_PARTIAL_HALT":
            return ["reduce_scope", "close_scope", "cancel"], ["open_new_scope", "increase_scope"]
        return ["cancel", "reduce_if_lcc_confirms", "close_if_lcc_confirms"], ["open_new", "increase"]

