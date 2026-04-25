from __future__ import annotations

from ai_hedge_bot.enforcement.schemas import risk_at_least


class ConsistencyValidator:
    def validate(self, context: dict) -> list[dict]:
        violations: list[dict] = []
        risk = str(context.get("orc_risk_level") or "L0_NORMAL")
        mode = str(context.get("governance_mode") or "NORMAL")
        execution = str(context.get("execution_mode") or "normal")
        if risk_at_least(risk, "L3_FREEZE") and mode not in {"SAFE_MODE", "RESTRICTED", "HALTED"}:
            violations.append({"type": "orc_afg_mismatch", "severity": "severe", "reason": "ORC L3+ requires AFG safe mode or stricter"})
        if risk_at_least(risk, "L3_FREEZE") and execution not in {"reduce_only", "partial_halt", "global_halt", "normal"}:
            violations.append({"type": "orc_execution_mismatch", "severity": "severe", "reason": "ORC L3+ requires execution reduce-only or stricter"})
        if risk == "L5_GLOBAL_HALT" and mode != "HALTED":
            violations.append({"type": "global_halt_afg_mismatch", "severity": "critical", "reason": "ORC L5 requires AFG HALTED"})
        return violations

