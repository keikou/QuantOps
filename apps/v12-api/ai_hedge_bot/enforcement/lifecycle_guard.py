from __future__ import annotations

from ai_hedge_bot.enforcement.schemas import risk_at_least


class LifecycleGuard:
    def check(self, request: dict, context: dict) -> dict:
        action = str(request.get("action_type") or "")
        status = str(context.get("approval_status") or "")
        risk = str(context.get("orc_risk_level") or "L0_NORMAL")
        mode = str(context.get("governance_mode") or "NORMAL")
        if action == "promote_alpha":
            if status != "approved":
                return {"decision": "REQUIRE_APPROVAL", "reason": "alpha_promotion_requires_approval", "constraints": {}, "violations": []}
            if mode != "NORMAL":
                return {"decision": "BLOCK", "reason": "non_normal_governance_mode_blocks_promotion", "constraints": {}, "violations": [{"type": "governance_mode_violation", "severity": "severe", "reason": mode}]}
        if action == "resume_alpha":
            if risk_at_least(risk, "L3_FREEZE"):
                return {"decision": "BLOCK", "reason": "orc_l3_plus_blocks_alpha_resume", "constraints": {}, "violations": [{"type": "safe_mode_violation", "severity": "severe", "reason": risk}]}
            if status != "approved":
                return {"decision": "REQUIRE_APPROVAL", "reason": "alpha_resume_requires_approval", "constraints": {}, "violations": []}
        if action == "retire_alpha" and status not in {"approved", "auto_applied"}:
            return {"decision": "REQUIRE_APPROVAL", "reason": "alpha_retirement_requires_approval", "constraints": {}, "violations": []}
        return {"decision": "ALLOW", "reason": "lifecycle_action_allowed", "constraints": {}, "violations": []}

