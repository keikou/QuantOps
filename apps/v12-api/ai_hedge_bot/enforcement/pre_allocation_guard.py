from __future__ import annotations

from ai_hedge_bot.enforcement.schemas import risk_at_least


class PreAllocationGuard:
    def check(self, request: dict, context: dict) -> dict:
        exposure_delta = float(request.get("exposure_delta") or 0.0)
        mode = str(context.get("governance_mode") or "NORMAL")
        risk = str(context.get("orc_risk_level") or "L0_NORMAL")
        if exposure_delta <= 0:
            return {"decision": "ALLOW", "reason": "risk_reducing_allocation_allowed", "constraints": {}, "violations": []}
        if mode in {"HALTED", "RESTRICTED"}:
            return {"decision": "BLOCK", "reason": "governance_mode_blocks_allocation_increase", "constraints": {}, "violations": [{"type": "governance_mode_violation", "severity": "severe", "reason": mode}]}
        if risk_at_least(risk, "L3_FREEZE"):
            return {"decision": "BLOCK", "reason": "orc_l3_plus_blocks_new_exposure", "constraints": {}, "violations": [{"type": "safe_mode_violation", "severity": "severe", "reason": risk}]}
        if not bool(context.get("lcc_available", True)):
            return {"decision": "BLOCK", "reason": "missing_lcc_state_blocks_allocation_increase", "constraints": {}, "violations": [{"type": "missing_lcc_state", "severity": "severe", "reason": "missing LCC context"}]}
        if not bool(context.get("lcc_allows_increase", True)):
            return {"decision": "ALLOW_WITH_CONSTRAINTS", "reason": "lcc_cap_constrains_allocation", "constraints": {"max_exposure_delta": 0.0}, "violations": []}
        return {"decision": "ALLOW", "reason": "allocation_allowed", "constraints": {}, "violations": []}

