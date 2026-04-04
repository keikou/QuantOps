from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from typing import Any

from ai_hedge_bot.services.policy_optimization_meta_control_learning_service import (
    PolicyOptimizationMetaControlLearningService,
)


class DeploymentRolloutIntelligenceService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.policy_optimization = PolicyOptimizationMetaControlLearningService()

    @staticmethod
    def _recommended_rollout_stage(
        *, realized_effect: str, tuning_action: str, observed_policy_cycles: int, coherent: bool
    ) -> tuple[str, str, list[str]]:
        if not coherent:
            return (
                "shadow",
                "blocked",
                [
                    "cross_layer_coherence_not_confirmed",
                    f"realized_effect:{realized_effect}",
                ],
            )
        if realized_effect == "adverse":
            return (
                "shadow",
                "blocked",
                [
                    "adverse_meta_policy_effect",
                    f"tuning_action:{tuning_action}",
                ],
            )
        if realized_effect == "neutral":
            return (
                "limited",
                "hold",
                [
                    "neutral_meta_policy_effect",
                    "collect_more_rollout_evidence",
                ],
            )
        if observed_policy_cycles >= 4 and tuning_action == "reinforce":
            return (
                "full",
                "eligible",
                [
                    "beneficial_meta_policy_effect",
                    "multi_cycle_confirmation_present",
                    "reinforcement_stable_enough_for_full_rollout",
                ],
            )
        if observed_policy_cycles >= 2:
            return (
                "canary",
                "eligible",
                [
                    "beneficial_meta_policy_effect",
                    "limited_multi_cycle_confirmation_present",
                ],
            )
        return (
            "limited",
            "eligible",
            [
                "beneficial_meta_policy_effect",
                "single_cycle_confirmation_only",
            ],
        )

    @staticmethod
    def _gating_conditions(stage: str) -> list[str]:
        gates = [
            "cross_layer_coherence:true",
            "runtime_control_checkpoint:C6",
            "portfolio_checkpoint:PI-05",
            "alpha_checkpoint:ASI-05",
            "research_checkpoint:RPI-06",
            "system_learning_checkpoint:SLLFI-05",
            "policy_optimization_checkpoint:PO-05",
        ]
        if stage in {"canary", "full"}:
            gates.append("realized_effect:beneficial")
        if stage == "full":
            gates.append("observed_policy_cycles>=4")
        return gates

    @staticmethod
    def _rollback_conditions(stage: str) -> list[str]:
        conditions = [
            "cross_layer_coherence:false",
            "realized_effect:adverse",
            "operator_override:rollback",
        ]
        if stage in {"canary", "full"}:
            conditions.append("beneficial_to_neutral_or_adverse_transition")
        if stage == "full":
            conditions.append("rollout_guardrail_breach")
        return conditions

    def latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.policy_optimization.outcome_effectiveness_latest(limit=limit)
        coherence = dict(payload.get("cross_layer_coherence") or {})
        coherent = bool(coherence.get("coherent", False))

        items: list[dict[str, Any]] = []
        shadow_count = 0
        limited_count = 0
        canary_count = 0
        full_count = 0
        eligible_count = 0
        hold_count = 0
        blocked_count = 0

        for item in list(payload.get("items") or []):
            realized_effect = str(item.get("realized_effect") or "neutral")
            tuning_action = str(item.get("tuning_action") or "hold")
            observed_policy_cycles = int(item.get("observed_policy_cycles", 0) or 0)
            stage, eligibility, stage_reason_codes = self._recommended_rollout_stage(
                realized_effect=realized_effect,
                tuning_action=tuning_action,
                observed_policy_cycles=observed_policy_cycles,
                coherent=coherent,
            )
            if stage == "shadow":
                shadow_count += 1
            elif stage == "limited":
                limited_count += 1
            elif stage == "canary":
                canary_count += 1
            elif stage == "full":
                full_count += 1

            if eligibility == "eligible":
                eligible_count += 1
            elif eligibility == "hold":
                hold_count += 1
            else:
                blocked_count += 1

            items.append(
                {
                    "alpha_family": item.get("alpha_family"),
                    "run_id": payload.get("run_id"),
                    "cycle_id": payload.get("cycle_id"),
                    "consumed_run_id": item.get("consumed_run_id"),
                    "consumed_cycle_id": item.get("consumed_cycle_id"),
                    "tuning_action": tuning_action,
                    "consumed_effect": item.get("consumed_effect"),
                    "intended_objective": item.get("intended_objective"),
                    "realized_effect": realized_effect,
                    "observed_policy_cycles": observed_policy_cycles,
                    "rollout_eligibility": eligibility,
                    "recommended_rollout_stage": stage,
                    "stage_reason_codes": stage_reason_codes,
                    "gating_conditions": self._gating_conditions(stage),
                    "rollback_conditions": self._rollback_conditions(stage),
                }
            )

        system_rollout_action = "hold_rollout_in_shadow"
        if blocked_count > 0:
            system_rollout_action = "rollback_blocked_families_to_shadow"
        elif hold_count > 0 and eligible_count == 0:
            system_rollout_action = "hold_limited_rollout_pending_more_evidence"
        elif canary_count > 0:
            system_rollout_action = "advance_eligible_families_to_canary"
        elif full_count == len(items) and full_count > 0:
            system_rollout_action = "promote_all_eligible_families_to_full"
        elif limited_count > 0 or eligible_count > 0:
            system_rollout_action = "advance_eligible_families_to_limited"

        return {
            "status": "ok",
            "run_id": payload.get("run_id"),
            "cycle_id": payload.get("cycle_id"),
            "mode": payload.get("mode"),
            "consumed_run_id": payload.get("consumed_run_id"),
            "consumed_cycle_id": payload.get("consumed_cycle_id"),
            "items": items,
            "cross_layer_coherence": coherence,
            "source_packets": {
                "execution_reality": "Packet 10",
                "governance_runtime_control": "C6",
                "portfolio_intelligence": "PI-05",
                "alpha_strategy_selection_intelligence": "ASI-05",
                "research_promotion_intelligence": "RPI-06",
                "system_learning_feedback_integration": "SLLFI-05",
                "policy_optimization_meta_control_learning": "PO-05",
            },
            "rollout_decision_summary": {
                "family_count": len(items),
                "eligible_families": eligible_count,
                "hold_families": hold_count,
                "blocked_families": blocked_count,
                "shadow_families": shadow_count,
                "limited_families": limited_count,
                "canary_families": canary_count,
                "full_families": full_count,
                "system_rollout_action": system_rollout_action,
            },
            "as_of": payload.get("as_of"),
        }

    def candidate_docket_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.latest(limit=limit)
        items: list[dict[str, Any]] = []
        ready_count = 0
        pending_count = 0
        denied_count = 0

        for item in list(payload.get("items") or []):
            stage = str(item.get("recommended_rollout_stage") or "shadow")
            eligibility = str(item.get("rollout_eligibility") or "hold")

            docket_status = "evidence_hold_candidate"
            deployment_action = "hold_limited_rollout"
            approval_status = "pending_evidence"
            rollout_priority = "normal"

            if eligibility == "blocked":
                docket_status = "blocked_candidate"
                deployment_action = "keep_in_shadow"
                approval_status = "denied"
                rollout_priority = "deprioritized"
                denied_count += 1
            elif stage == "full":
                docket_status = "full_rollout_candidate"
                deployment_action = "prepare_full_rollout"
                approval_status = "ready_for_review"
                rollout_priority = "high"
                ready_count += 1
            elif stage == "canary":
                docket_status = "canary_rollout_candidate"
                deployment_action = "prepare_canary_rollout"
                approval_status = "ready_for_review"
                rollout_priority = "high"
                ready_count += 1
            elif stage == "limited" and eligibility == "eligible":
                docket_status = "limited_rollout_candidate"
                deployment_action = "prepare_limited_rollout"
                approval_status = "ready_for_review"
                rollout_priority = "normal"
                ready_count += 1
            else:
                pending_count += 1

            items.append(
                {
                    **item,
                    "approval_status": approval_status,
                    "docket_status": docket_status,
                    "deployment_action": deployment_action,
                    "rollout_priority": rollout_priority,
                    "checkpoint_lineage": {
                        "execution_reality": "Packet 10",
                        "governance_runtime_control": "C6",
                        "portfolio_intelligence": "PI-05",
                        "alpha_strategy_selection_intelligence": "ASI-05",
                        "research_promotion_intelligence": "RPI-06",
                        "system_learning_feedback_integration": "SLLFI-05",
                        "policy_optimization_meta_control_learning": "PO-05",
                        "deployment_rollout_intelligence": "DRI-01",
                    },
                }
            )

        system_docket_action = "hold_rollout_docket_for_more_evidence"
        if denied_count > 0:
            system_docket_action = "exclude_blocked_candidates_from_rollout_docket"
        elif ready_count > 0:
            system_docket_action = "submit_ready_candidates_for_rollout_review"

        return {
            "status": "ok",
            "run_id": payload.get("run_id"),
            "cycle_id": payload.get("cycle_id"),
            "mode": payload.get("mode"),
            "consumed_run_id": payload.get("consumed_run_id"),
            "consumed_cycle_id": payload.get("consumed_cycle_id"),
            "items": items,
            "cross_layer_coherence": payload.get("cross_layer_coherence") or {},
            "source_packets": payload.get("source_packets") or {},
            "rollout_decision_summary": payload.get("rollout_decision_summary") or {},
            "candidate_docket_summary": {
                "family_count": len(items),
                "ready_for_review_families": ready_count,
                "pending_evidence_families": pending_count,
                "denied_families": denied_count,
                "system_docket_action": system_docket_action,
            },
            "as_of": payload.get("as_of"),
        }

    def persisted_rollout_state_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.candidate_docket_latest(limit=limit)
        created_at = utc_now_iso()
        items: list[dict[str, Any]] = []

        for item in list(payload.get("items") or []):
            family = str(item.get("alpha_family") or "unknown")
            previous_state = self.store.fetchone_dict(
                """
                SELECT *
                FROM audit_logs
                WHERE category='deployment_rollout_state'
                  AND actor=?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                [family],
            ) or {}
            rollout_state_id = new_cycle_id()
            self.store.append(
                "audit_logs",
                {
                    "audit_id": rollout_state_id,
                    "created_at": created_at,
                    "category": "deployment_rollout_state",
                    "event_type": "persist_rollout_state",
                    "run_id": payload.get("run_id"),
                    "payload_json": self.store.to_json(
                        {
                            "alpha_family": family,
                            "run_id": payload.get("run_id"),
                            "cycle_id": payload.get("cycle_id"),
                            "mode": payload.get("mode"),
                            "recommended_rollout_stage": item.get("recommended_rollout_stage"),
                            "rollout_eligibility": item.get("rollout_eligibility"),
                            "approval_status": item.get("approval_status"),
                            "docket_status": item.get("docket_status"),
                            "deployment_action": item.get("deployment_action"),
                            "rollout_priority": item.get("rollout_priority"),
                            "rollout_source_packet": "DRI-02",
                        }
                    ),
                    "actor": family,
                },
            )
            items.append(
                {
                    **item,
                    "rollout_state_id": rollout_state_id,
                    "previous_rollout_state_id": previous_state.get("audit_id"),
                    "rollout_state_timestamp": created_at,
                    "rollout_source_packet": "DRI-02",
                }
            )

        return {
            "status": "ok",
            "run_id": payload.get("run_id"),
            "cycle_id": payload.get("cycle_id"),
            "mode": payload.get("mode"),
            "consumed_run_id": payload.get("consumed_run_id"),
            "consumed_cycle_id": payload.get("consumed_cycle_id"),
            "items": items,
            "cross_layer_coherence": payload.get("cross_layer_coherence") or {},
            "source_packets": payload.get("source_packets") or {},
            "rollout_decision_summary": payload.get("rollout_decision_summary") or {},
            "candidate_docket_summary": payload.get("candidate_docket_summary") or {},
            "persisted_rollout_state_summary": {
                "family_count": len(items),
                "persisted_states": len(items),
                "system_rollout_state_action": "persist_rollout_candidate_state",
            },
            "as_of": created_at,
        }

    def applied_rollout_consumption_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.persisted_rollout_state_latest(limit=limit)
        consumed_run_id = f"{payload.get('run_id') or 'unknown'}:rollout-next"
        consumed_cycle_id = f"{payload.get('cycle_id') or 'unknown'}:rollout-next"
        items: list[dict[str, Any]] = []
        shadow_count = 0
        limited_count = 0
        canary_count = 0
        full_count = 0

        for item in list(payload.get("items") or []):
            stage = str(item.get("recommended_rollout_stage") or "shadow")
            eligibility = str(item.get("rollout_eligibility") or "hold")
            approval_status = str(item.get("approval_status") or "pending_evidence")

            rollout_profile = {
                "consumed": True,
                "consumed_run_id": consumed_run_id,
                "consumed_cycle_id": consumed_cycle_id,
                "applied_stage": stage,
                "applied_approval_status": approval_status,
                "applied_deployment_action": item.get("deployment_action"),
            }

            consumed_effect = "rollout_shadow_hold_applied"
            if stage == "full" and eligibility == "eligible":
                consumed_effect = "rollout_full_activation_applied"
                full_count += 1
            elif stage == "canary" and eligibility == "eligible":
                consumed_effect = "rollout_canary_activation_applied"
                canary_count += 1
            elif stage == "limited":
                consumed_effect = (
                    "rollout_limited_activation_applied"
                    if eligibility == "eligible"
                    else "rollout_limited_hold_applied"
                )
                limited_count += 1
            else:
                shadow_count += 1

            items.append(
                {
                    **item,
                    "consumed_run_id": consumed_run_id,
                    "consumed_cycle_id": consumed_cycle_id,
                    "applied_rollout_consumption": rollout_profile,
                    "consumed_effect": consumed_effect,
                }
            )

        system_consumption_action = "apply_shadow_rollout_posture"
        if full_count > 0:
            system_consumption_action = "apply_full_rollout_for_ready_families"
        elif canary_count > 0:
            system_consumption_action = "apply_canary_rollout_for_ready_families"
        elif limited_count > 0:
            system_consumption_action = "apply_limited_rollout_posture"

        return {
            "status": "ok",
            "run_id": payload.get("run_id"),
            "cycle_id": payload.get("cycle_id"),
            "mode": payload.get("mode"),
            "consumed_run_id": consumed_run_id,
            "consumed_cycle_id": consumed_cycle_id,
            "items": items,
            "cross_layer_coherence": payload.get("cross_layer_coherence") or {},
            "source_packets": payload.get("source_packets") or {},
            "rollout_decision_summary": payload.get("rollout_decision_summary") or {},
            "candidate_docket_summary": payload.get("candidate_docket_summary") or {},
            "persisted_rollout_state_summary": payload.get("persisted_rollout_state_summary") or {},
            "applied_rollout_consumption_summary": {
                "family_count": len(items),
                "shadow_consumptions": shadow_count,
                "limited_consumptions": limited_count,
                "canary_consumptions": canary_count,
                "full_consumptions": full_count,
                "system_consumption_action": system_consumption_action,
            },
            "as_of": payload.get("as_of"),
        }

    def rollout_outcome_effectiveness_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.applied_rollout_consumption_latest(limit=limit)
        items: list[dict[str, Any]] = []
        beneficial_count = 0
        neutral_count = 0
        adverse_count = 0

        for item in list(payload.get("items") or []):
            stage = str(item.get("recommended_rollout_stage") or "shadow")
            eligibility = str(item.get("rollout_eligibility") or "hold")
            consumed_effect = str(item.get("consumed_effect") or "rollout_shadow_hold_applied")
            realized_effect = "neutral"

            if stage == "full" and eligibility == "eligible":
                realized_effect = "beneficial"
                beneficial_count += 1
            elif stage == "canary" and eligibility == "eligible":
                realized_effect = "beneficial"
                beneficial_count += 1
            elif stage == "limited":
                realized_effect = "neutral"
                neutral_count += 1
            else:
                realized_effect = "adverse"
                adverse_count += 1

            items.append(
                {
                    **item,
                    "intended_objective": "improve_rollout_safety_and_progression",
                    "realized_effect": realized_effect,
                    "effectiveness_reason_codes": [
                        f"recommended_rollout_stage:{stage}",
                        f"rollout_eligibility:{eligibility}",
                        f"consumed_effect:{consumed_effect}",
                        f"realized_effect:{realized_effect}",
                    ],
                }
            )

        system_effectiveness_action = "observe_rollout_effectiveness"
        if adverse_count > 0:
            system_effectiveness_action = "rework_adverse_rollout_posture"
        elif beneficial_count > 0:
            system_effectiveness_action = "reinforce_effective_rollout_posture"

        return {
            "status": "ok",
            "run_id": payload.get("run_id"),
            "cycle_id": payload.get("cycle_id"),
            "mode": payload.get("mode"),
            "consumed_run_id": payload.get("consumed_run_id"),
            "consumed_cycle_id": payload.get("consumed_cycle_id"),
            "items": items,
            "cross_layer_coherence": payload.get("cross_layer_coherence") or {},
            "source_packets": payload.get("source_packets") or {},
            "rollout_decision_summary": payload.get("rollout_decision_summary") or {},
            "candidate_docket_summary": payload.get("candidate_docket_summary") or {},
            "persisted_rollout_state_summary": payload.get("persisted_rollout_state_summary") or {},
            "applied_rollout_consumption_summary": payload.get("applied_rollout_consumption_summary") or {},
            "rollout_outcome_effectiveness_summary": {
                "family_count": len(items),
                "beneficial_families": beneficial_count,
                "neutral_families": neutral_count,
                "adverse_families": adverse_count,
                "system_effectiveness_action": system_effectiveness_action,
            },
            "as_of": payload.get("as_of"),
        }
