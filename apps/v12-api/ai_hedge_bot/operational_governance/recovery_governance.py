from __future__ import annotations

from ai_hedge_bot.core.ids import new_run_id


class RecoveryGovernance:
    def build_request(
        self,
        source_incident_id: str,
        current_risk_level: str,
        requested_target_level: str,
        readiness_passed: bool,
        now: str,
    ) -> dict:
        approval_required = current_risk_level in {"L4_PARTIAL_HALT", "L5_GLOBAL_HALT"}
        return {
            "recovery_id": new_run_id(),
            "source_incident_id": source_incident_id,
            "current_risk_level": current_risk_level,
            "requested_target_level": requested_target_level,
            "readiness_passed": readiness_passed,
            "approval_required": approval_required,
            "approval_id": new_run_id() if approval_required else "",
            "status": "approval_pending" if approval_required else "approved_for_recovery",
            "reason": "operator_recovery_request",
            "created_at": now,
            "decided_at": None if approval_required else now,
        }

