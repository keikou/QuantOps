from __future__ import annotations


class PolicyGateEngine:
    def evaluate(
        self,
        source_system: str,
        action_type: str,
        target_type: str,
        risk_level: str,
        governance_mode: str = "NORMAL",
        operator_id: str = "",
        reason: str = "",
    ) -> dict:
        if not source_system or not action_type or not target_type:
            return self._decision("BLOCK", "malformed_policy_input")
        if source_system == "Operator" and action_type in {"override", "force_apply", "global_halt"}:
            if not operator_id:
                return self._decision("BLOCK", "manual_high_risk_action_requires_operator_id")
            if not reason:
                return self._decision("BLOCK", "manual_high_risk_action_requires_reason")
        if governance_mode == "HALTED" and action_type in {"promote_alpha", "increase_exposure", "weight_increase"}:
            return self._decision("BLOCK", "halted_mode_blocks_risk_increase")
        if source_system == "ORC":
            if risk_level in {"L0_NORMAL", "L1_WATCH"}:
                return self._decision("AUTO_RECORD", "orc_low_risk_audit_only")
            if risk_level in {"L2_REDUCE", "L3_FREEZE"}:
                return self._decision("AUTO_APPLY", "orc_reduce_or_freeze_auto_policy")
            if risk_level in {"L4_PARTIAL_HALT", "L5_GLOBAL_HALT"}:
                return self._decision("REQUIRE_APPROVAL", "orc_high_risk_requires_operator_approval")
        if source_system in {"AES-08", "AES"} and action_type in {"policy_update", "threshold_update"}:
            return self._decision("REQUIRE_APPROVAL", "alpha_policy_change_requires_approval")
        if source_system == "AES-07" and action_type in {"retire_alpha", "freeze_alpha"}:
            return self._decision("REQUIRE_APPROVAL", "alpha_retirement_requires_approval")
        if source_system == "AAE" and action_type == "promote_alpha":
            return self._decision("REQUIRE_APPROVAL", "production_promotion_requires_approval")
        return self._decision("AUTO_RECORD", "default_audit_only")

    def _decision(self, decision: str, reason: str) -> dict:
        return {
            "decision": decision,
            "reason": reason,
            "requires_approval": decision == "REQUIRE_APPROVAL",
            "blocked": decision == "BLOCK",
            "auto_apply": decision == "AUTO_APPLY",
            "audit_required": True,
        }

