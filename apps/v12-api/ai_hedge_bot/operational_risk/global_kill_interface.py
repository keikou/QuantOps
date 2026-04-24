from __future__ import annotations

from ai_hedge_bot.core.ids import new_run_id


class GlobalKillInterface:
    def build_event(
        self,
        run_id: str | None,
        trigger_source: str,
        trigger_reason: str,
        risk_level: str,
        kill_scope: str,
        operator_id: str = "system",
    ) -> dict:
        return {
            "event_id": new_run_id(),
            "run_id": run_id,
            "trigger_source": trigger_source,
            "trigger_reason": trigger_reason,
            "risk_level": risk_level,
            "kill_scope": kill_scope,
            "state_before": "active",
            "state_after": risk_level,
            "operator_id": operator_id,
            "reversible": risk_level != "L5_GLOBAL_HALT",
        }

