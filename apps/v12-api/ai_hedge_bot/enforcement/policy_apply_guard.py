from __future__ import annotations


class PolicyApplyGuard:
    def check(self, request: dict, context: dict) -> dict:
        action = str(request.get("action_type") or "")
        status = str(context.get("approval_status") or "")
        mode = str(context.get("governance_mode") or "NORMAL")
        if action == "policy_tightening":
            return {"decision": "ALLOW", "reason": "policy_tightening_allowed", "constraints": {}, "violations": []}
        if action == "policy_relaxation":
            if mode in {"SAFE_MODE", "RESTRICTED", "HALTED"}:
                return {"decision": "BLOCK", "reason": "policy_relaxation_blocked_in_elevated_mode", "constraints": {}, "violations": [{"type": "policy_relaxation_violation", "severity": "severe", "reason": mode}]}
            if status != "approved":
                return {"decision": "REQUIRE_APPROVAL", "reason": "policy_relaxation_requires_approval", "constraints": {}, "violations": []}
        if action in {"threshold_update", "generation_prior_update"} and status != "approved":
            return {"decision": "REQUIRE_APPROVAL", "reason": "policy_update_requires_approval", "constraints": {}, "violations": []}
        return {"decision": "ALLOW", "reason": "policy_apply_allowed", "constraints": {}, "violations": []}

