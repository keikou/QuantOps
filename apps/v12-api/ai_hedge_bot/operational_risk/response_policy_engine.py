from __future__ import annotations


class ResponsePolicyEngine:
    def build(self, state: dict, incident_id: str | None = None) -> dict:
        level = str(state["global_risk_level"])
        return {
            "incident_id": incident_id,
            "action_type": state["recommended_action"],
            "target_scope": "global" if level in {"L4_PARTIAL_HALT", "L5_GLOBAL_HALT"} else "system",
            "target_id": "quantops",
            "requested_by": "ORC",
            "approved": level in {"L1_WATCH", "L2_REDUCE", "L3_FREEZE"},
            "executed": False,
            "execution_status": "pending_execution",
            "reason": f"orc_recommended_{level}",
        }

