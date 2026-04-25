from __future__ import annotations

from ai_hedge_bot.enforcement.schemas import RISK_INCREASING_ORDER_MODES, RISK_REDUCING_ORDER_MODES, risk_at_least


class PreExecutionGuard:
    def check(self, request: dict, context: dict) -> dict:
        mode = str(request.get("order_mode") or request.get("action_type") or "")
        risk = str(context.get("orc_risk_level") or "L0_NORMAL")
        governance_mode = str(context.get("governance_mode") or "NORMAL")
        if governance_mode in {"HALTED", "RESTRICTED"} and mode in RISK_INCREASING_ORDER_MODES:
            return {"decision": "BLOCK", "reason": "governance_mode_blocks_risk_increasing_order", "constraints": {"allowed_order_modes": sorted(RISK_REDUCING_ORDER_MODES)}, "violations": [{"type": "governance_mode_violation", "severity": "severe", "reason": governance_mode}]}
        if not bool(context.get("execution_state_available", True)) and mode in RISK_INCREASING_ORDER_MODES:
            return {"decision": "BLOCK", "reason": "missing_execution_state_blocks_risk_increasing_order", "constraints": {}, "violations": [{"type": "missing_execution_state", "severity": "severe", "reason": mode}]}
        if risk == "L5_GLOBAL_HALT":
            if mode in RISK_REDUCING_ORDER_MODES and bool(context.get("lcc_confirms_risk_reduction", True)):
                return {"decision": "ALLOW_WITH_CONSTRAINTS", "reason": "l5_allows_confirmed_risk_reducing_order", "constraints": {"allowed_order_modes": sorted(RISK_REDUCING_ORDER_MODES)}, "violations": []}
            return {"decision": "BLOCK", "reason": "l5_global_halt_blocks_order", "constraints": {"allowed_order_modes": sorted(RISK_REDUCING_ORDER_MODES)}, "violations": [{"type": "global_halt_violation", "severity": "critical", "reason": mode}]}
        if risk_at_least(risk, "L3_FREEZE") and mode in RISK_INCREASING_ORDER_MODES:
            return {"decision": "BLOCK", "reason": f"{risk}_blocks_{mode}", "constraints": {"allowed_order_modes": sorted(RISK_REDUCING_ORDER_MODES)}, "violations": [{"type": "safe_mode_violation", "severity": "severe", "reason": mode}]}
        return {"decision": "ALLOW", "reason": "execution_allowed", "constraints": {}, "violations": []}
