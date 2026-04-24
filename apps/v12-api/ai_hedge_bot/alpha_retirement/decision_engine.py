from __future__ import annotations

from ai_hedge_bot.alpha_retirement.schemas import RetirementInput


class RetirementDecisionEngine:
    def decide(self, item: RetirementInput, health: dict) -> dict:
        health_score = float(health["health_score"])
        pressure = float(health["deactivation_pressure"])
        if health_score < 0.30 or pressure > 0.72:
            decision = "retire_alpha"
            kill_switch_action = "deactivate"
        elif health_score < 0.45 or item.crowding_penalty > 0.82:
            decision = "freeze_alpha"
            kill_switch_action = "freeze"
        elif health_score < 0.60 or item.weight_change_reason in {"risk_or_capacity_reduction", "capacity_block"}:
            decision = "reduce_alpha"
            kill_switch_action = "reduce"
        else:
            decision = "continue_alpha"
            kill_switch_action = "continue"
        return {
            "decision": decision,
            "kill_switch_action": kill_switch_action,
            "decision_reason": self._reason(item, health),
        }

    def _reason(self, item: RetirementInput, health: dict) -> str:
        if item.crowding_penalty > 0.82:
            return "crowding_spike"
        if item.impact_penalty > 0.55:
            return "impact_degradation"
        if item.live_evidence_score < 0.45:
            return "weak_live_evidence"
        if item.weight_change_reason in {"risk_or_capacity_reduction", "capacity_block"}:
            return item.weight_change_reason
        return "within_runtime_tolerance"
