from __future__ import annotations

import json
from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.services.system_level_learning_feedback_integration_service import (
    SystemLevelLearningFeedbackIntegrationService,
)


class PolicyOptimizationMetaControlLearningService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.system_learning = SystemLevelLearningFeedbackIntegrationService()

    @staticmethod
    def _effect_from_counts(beneficial: int, adverse: int) -> str:
        if beneficial > adverse:
            return "beneficial"
        if adverse > beneficial:
            return "adverse"
        return "neutral"

    @staticmethod
    def _path_classification(*, applied_value: Any, effect_classification: str, neutral_value: Any) -> str:
        if applied_value == neutral_value:
            return "neutral"
        return effect_classification

    @staticmethod
    def _attribution_reason_codes(
        *,
        effect_classification: str,
        consumed_effect: str,
        override_state: str,
        beneficial: int,
        adverse: int,
        transition_count: int,
        observed_policy_cycles: int,
    ) -> list[str]:
        reason_codes = [f"consumed_effect:{consumed_effect}", f"override_state:{override_state}"]
        if beneficial > 0:
            reason_codes.append("beneficial_downstream_feedback_present")
        if adverse > 0:
            reason_codes.append("adverse_downstream_feedback_present")
        if transition_count > 0:
            reason_codes.append("governed_transition_evidence_present")
        if observed_policy_cycles > 1:
            reason_codes.append("multi_cycle_policy_history_present")
        reason_codes.append(f"policy_effect:{effect_classification}")
        return reason_codes

    def _policy_history_by_family(self) -> dict[str, dict[str, Any]]:
        rows = self.store.fetchall_dict(
            """
            SELECT actor, audit_id, created_at, payload_json
            FROM audit_logs
            WHERE category='system_learning_policy_state'
            ORDER BY created_at DESC, rowid DESC
            """
        )
        families: dict[str, dict[str, Any]] = {}
        for row in rows:
            family = str(row.get("actor") or "unknown")
            try:
                payload = json.loads(str(row.get("payload_json") or "{}"))
            except json.JSONDecodeError:
                payload = {}
            history = families.setdefault(
                family,
                {
                    "alpha_family": family,
                    "policy_state_ids": [],
                    "applied_learning_actions": [],
                    "latest_policy_state_id": None,
                    "latest_policy_timestamp": None,
                },
            )
            history["policy_state_ids"].append(str(row.get("audit_id") or ""))
            history["applied_learning_actions"].append(str(payload.get("applied_learning_action") or "observe"))
            if history["latest_policy_state_id"] is None:
                history["latest_policy_state_id"] = row.get("audit_id")
                history["latest_policy_timestamp"] = row.get("created_at")
        for history in families.values():
            history["observed_policy_cycles"] = len(list(history.get("policy_state_ids") or []))
        return families

    def latest(self, limit: int = 20) -> dict[str, Any]:
        applied_payload = self.system_learning.applied_override_consumption_latest(limit=limit)
        feedback_payload = self.system_learning.latest(limit=limit)
        policy_history = self._policy_history_by_family()

        feedback_by_family = {
            str(item.get("alpha_family") or ""): item for item in list(feedback_payload.get("items") or [])
        }
        items: list[dict[str, Any]] = []
        beneficial_count = 0
        neutral_count = 0
        adverse_count = 0

        for item in list(applied_payload.get("items") or []):
            family = str(item.get("alpha_family") or "unknown")
            feedback_item = dict(feedback_by_family.get(family) or {})
            history_item = dict(policy_history.get(family) or {})
            portfolio_feedback = dict(feedback_item.get("portfolio_feedback") or {})
            transition_feedback = dict(feedback_item.get("governed_transition_feedback") or {})

            beneficial = int(portfolio_feedback.get("beneficial_actions", 0) or 0)
            adverse = int(portfolio_feedback.get("adverse_actions", 0) or 0)
            transition_count = (
                int(transition_feedback.get("promoted_states", 0) or 0)
                + int(transition_feedback.get("shadow_states", 0) or 0)
                + int(transition_feedback.get("retired_states", 0) or 0)
                + int(transition_feedback.get("rejected_states", 0) or 0)
                + int(transition_feedback.get("candidate_states", 0) or 0)
            )
            observed_policy_cycles = int(history_item.get("observed_policy_cycles", 0) or 0)
            effect_classification = self._effect_from_counts(beneficial, adverse)
            if effect_classification == "beneficial":
                beneficial_count += 1
            elif effect_classification == "adverse":
                adverse_count += 1
            else:
                neutral_count += 1

            selection_consumption = dict(item.get("selection_consumption") or {})
            capital_consumption = dict(item.get("capital_consumption") or {})
            review_consumption = dict(item.get("review_consumption") or {})
            runtime_consumption = dict(item.get("runtime_consumption") or {})
            consumed_effect = str(item.get("consumed_effect") or "neutral_consumption")
            override_state = str(item.get("override_state") or "neutral")

            items.append(
                {
                    "alpha_family": family,
                    "run_id": applied_payload.get("run_id"),
                    "cycle_id": applied_payload.get("cycle_id"),
                    "consumed_run_id": item.get("consumed_run_id"),
                    "consumed_cycle_id": item.get("consumed_cycle_id"),
                    "latest_policy_state_id": history_item.get("latest_policy_state_id"),
                    "latest_policy_timestamp": history_item.get("latest_policy_timestamp"),
                    "observed_policy_cycles": observed_policy_cycles,
                    "consumed_effect": consumed_effect,
                    "effect_classification": effect_classification,
                    "intended_vs_realized": {
                        "intended_effect": "improve_downstream_policy_quality",
                        "realized_effect": effect_classification,
                        "attribution_basis": "applied_policy_path",
                    },
                    "policy_paths": {
                        "selection": {
                            "intended_improvement": "improve_strategy_selection_quality",
                            "applied_adjustment": float(selection_consumption.get("applied_score_adjustment", 0.0) or 0.0),
                            "applied_bias": str(selection_consumption.get("applied_selection_bias") or "neutral"),
                            "effect_classification": self._path_classification(
                                applied_value=float(selection_consumption.get("applied_score_adjustment", 0.0) or 0.0),
                                effect_classification=effect_classification,
                                neutral_value=0.0,
                            ),
                        },
                        "capital": {
                            "intended_improvement": "improve_capital_allocation_quality",
                            "applied_multiplier": float(capital_consumption.get("applied_capital_multiplier", 1.0) or 1.0),
                            "applied_bias": str(capital_consumption.get("applied_capital_bias") or "hold"),
                            "effect_classification": self._path_classification(
                                applied_value=float(capital_consumption.get("applied_capital_multiplier", 1.0) or 1.0),
                                effect_classification=effect_classification,
                                neutral_value=1.0,
                            ),
                        },
                        "review": {
                            "intended_improvement": "improve_review_pressure_quality",
                            "applied_pressure": str(review_consumption.get("applied_review_pressure") or "hold"),
                            "effect_classification": self._path_classification(
                                applied_value=str(review_consumption.get("applied_review_pressure") or "hold"),
                                effect_classification=effect_classification,
                                neutral_value="hold",
                            ),
                        },
                        "runtime": {
                            "intended_improvement": "improve_runtime_control_quality",
                            "applied_caution": str(runtime_consumption.get("applied_runtime_caution") or "normal"),
                            "effect_classification": self._path_classification(
                                applied_value=str(runtime_consumption.get("applied_runtime_caution") or "normal"),
                                effect_classification=effect_classification,
                                neutral_value="normal",
                            ),
                        },
                    },
                    "downstream_feedback": {
                        "beneficial_actions": beneficial,
                        "neutral_actions": int(portfolio_feedback.get("neutral_actions", 0) or 0),
                        "adverse_actions": adverse,
                        "drag_change_usd_total": round(float(portfolio_feedback.get("drag_change_usd_total", 0.0) or 0.0), 6),
                        "resolved_weight_change_total": round(float(portfolio_feedback.get("resolved_weight_change_total", 0.0) or 0.0), 6),
                        "concentration_change_total": round(float(portfolio_feedback.get("concentration_change_total", 0.0) or 0.0), 6),
                        "governed_transition_count": transition_count,
                    },
                    "attribution_reason_codes": self._attribution_reason_codes(
                        effect_classification=effect_classification,
                        consumed_effect=consumed_effect,
                        override_state=override_state,
                        beneficial=beneficial,
                        adverse=adverse,
                        transition_count=transition_count,
                        observed_policy_cycles=observed_policy_cycles,
                    ),
                }
            )

        system_policy_optimization_action = "observe_policy_effectiveness"
        if adverse_count > 0:
            system_policy_optimization_action = "retune_adverse_policy_families"
        elif neutral_count > 0:
            system_policy_optimization_action = "collect_more_policy_evidence"
        elif beneficial_count > 0:
            system_policy_optimization_action = "reinforce_beneficial_policy_families"

        return {
            "status": "ok",
            "run_id": applied_payload.get("run_id"),
            "cycle_id": applied_payload.get("cycle_id"),
            "mode": applied_payload.get("mode"),
            "consumed_run_id": applied_payload.get("consumed_run_id"),
            "consumed_cycle_id": applied_payload.get("consumed_cycle_id"),
            "items": items,
            "cross_layer_coherence": applied_payload.get("cross_layer_coherence") or {},
            "source_packets": {
                "system_learning_feedback": "SLLFI-01",
                "policy_updates": "SLLFI-02",
                "persisted_policy_state": "SLLFI-03",
                "resolved_overrides": "SLLFI-04",
                "applied_consumption": "SLLFI-05",
            },
            "policy_effectiveness_summary": {
                "family_count": len(items),
                "beneficial_families": beneficial_count,
                "neutral_families": neutral_count,
                "adverse_families": adverse_count,
                "system_policy_optimization_action": system_policy_optimization_action,
            },
            "as_of": applied_payload.get("as_of"),
        }

    def tuning_recommendations_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.latest(limit=limit)
        items: list[dict[str, Any]] = []
        reinforce_count = 0
        hold_count = 0
        retune_count = 0

        for item in list(payload.get("items") or []):
            effect_classification = str(item.get("effect_classification") or "neutral")
            observed_policy_cycles = int(item.get("observed_policy_cycles", 0) or 0)
            tuning_action = "hold"
            threshold_adjustment = 0.0
            weight_adjustment = 0.0
            escalation_rule = "keep"

            if effect_classification == "beneficial":
                tuning_action = "reinforce"
                threshold_adjustment = 0.05
                weight_adjustment = 0.08
                escalation_rule = "relax"
                reinforce_count += 1
            elif effect_classification == "adverse":
                tuning_action = "retune"
                threshold_adjustment = -0.08
                weight_adjustment = -0.12
                escalation_rule = "tighten"
                retune_count += 1
            else:
                hold_count += 1
                if observed_policy_cycles <= 1:
                    escalation_rule = "collect_more_evidence"

            items.append(
                {
                    **item,
                    "tuning_action": tuning_action,
                    "tuning_adjustments": {
                        "threshold_adjustment": threshold_adjustment,
                        "weight_adjustment": weight_adjustment,
                        "escalation_rule": escalation_rule,
                    },
                }
            )

        system_tuning_action = "hold_current_policy_tuning"
        if retune_count > 0:
            system_tuning_action = "retune_adverse_policy_families"
        elif reinforce_count > 0:
            system_tuning_action = "reinforce_beneficial_policy_families"
        elif hold_count > 0:
            system_tuning_action = "collect_more_policy_evidence"

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
            "policy_effectiveness_summary": payload.get("policy_effectiveness_summary") or {},
            "tuning_summary": {
                "family_count": len(items),
                "reinforce_families": reinforce_count,
                "hold_families": hold_count,
                "retune_families": retune_count,
                "system_tuning_action": system_tuning_action,
            },
            "as_of": payload.get("as_of"),
        }

    def persisted_meta_policy_state_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.tuning_recommendations_latest(limit=limit)
        created_at = utc_now_iso()
        items: list[dict[str, Any]] = []

        for item in list(payload.get("items") or []):
            family = str(item.get("alpha_family") or "unknown")
            previous_state = self.store.fetchone_dict(
                """
                SELECT *
                FROM audit_logs
                WHERE category='meta_policy_state'
                  AND actor=?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                [family],
            ) or {}
            state_id = new_cycle_id()
            tuning_adjustments = dict(item.get("tuning_adjustments") or {})
            self.store.append(
                "audit_logs",
                {
                    "audit_id": state_id,
                    "created_at": created_at,
                    "category": "meta_policy_state",
                    "event_type": "persist_meta_policy_state",
                    "run_id": payload.get("run_id"),
                    "payload_json": self.store.to_json(
                        {
                            "alpha_family": family,
                            "run_id": payload.get("run_id"),
                            "cycle_id": payload.get("cycle_id"),
                            "mode": payload.get("mode"),
                            "effect_classification": item.get("effect_classification"),
                            "tuning_action": item.get("tuning_action"),
                            "threshold_adjustment": tuning_adjustments.get("threshold_adjustment"),
                            "weight_adjustment": tuning_adjustments.get("weight_adjustment"),
                            "escalation_rule": tuning_adjustments.get("escalation_rule"),
                            "policy_source_packet": "PO-02",
                        }
                    ),
                    "actor": family,
                },
            )
            items.append(
                {
                    **item,
                    "meta_policy_state_id": state_id,
                    "previous_meta_policy_state_id": previous_state.get("audit_id"),
                    "meta_policy_timestamp": created_at,
                    "policy_source_packet": "PO-02",
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
            "policy_effectiveness_summary": payload.get("policy_effectiveness_summary") or {},
            "tuning_summary": payload.get("tuning_summary") or {},
            "persisted_meta_policy_summary": {
                "family_count": len(items),
                "persisted_states": len(items),
                "system_meta_policy_action": "persist_meta_policy_tuning_state",
            },
            "as_of": created_at,
        }

    def applied_tuning_consumption_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.persisted_meta_policy_state_latest(limit=limit)
        consumed_run_id = f"{payload.get('run_id') or 'unknown'}:meta-next"
        consumed_cycle_id = f"{payload.get('cycle_id') or 'unknown'}:meta-next"
        items: list[dict[str, Any]] = []
        reinforce_count = 0
        hold_count = 0
        retune_count = 0

        for item in list(payload.get("items") or []):
            tuning_action = str(item.get("tuning_action") or "hold")
            tuning_adjustments = dict(item.get("tuning_adjustments") or {})
            consumed_effect = "meta_policy_hold_applied"
            if tuning_action == "reinforce":
                consumed_effect = "meta_policy_reinforcement_applied"
                reinforce_count += 1
            elif tuning_action == "retune":
                consumed_effect = "meta_policy_retune_applied"
                retune_count += 1
            else:
                hold_count += 1

            items.append(
                {
                    **item,
                    "consumed_run_id": consumed_run_id,
                    "consumed_cycle_id": consumed_cycle_id,
                    "applied_tuning_consumption": {
                        "consumed": True,
                        "consumed_run_id": consumed_run_id,
                        "consumed_cycle_id": consumed_cycle_id,
                        "applied_threshold_adjustment": tuning_adjustments.get("threshold_adjustment", 0.0),
                        "applied_weight_adjustment": tuning_adjustments.get("weight_adjustment", 0.0),
                        "applied_escalation_rule": tuning_adjustments.get("escalation_rule", "keep"),
                    },
                    "consumed_effect": consumed_effect,
                }
            )

        system_consumption_action = "apply_hold_meta_policy"
        if retune_count > 0:
            system_consumption_action = "apply_retuned_meta_policy"
        elif reinforce_count > 0:
            system_consumption_action = "apply_reinforced_meta_policy"

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
            "policy_effectiveness_summary": payload.get("policy_effectiveness_summary") or {},
            "tuning_summary": payload.get("tuning_summary") or {},
            "persisted_meta_policy_summary": payload.get("persisted_meta_policy_summary") or {},
            "applied_tuning_consumption_summary": {
                "family_count": len(items),
                "reinforced_consumptions": reinforce_count,
                "hold_consumptions": hold_count,
                "retuned_consumptions": retune_count,
                "system_consumption_action": system_consumption_action,
            },
            "as_of": payload.get("as_of"),
        }

    def outcome_effectiveness_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.applied_tuning_consumption_latest(limit=limit)
        items: list[dict[str, Any]] = []
        beneficial_count = 0
        neutral_count = 0
        adverse_count = 0

        for item in list(payload.get("items") or []):
            tuning_action = str(item.get("tuning_action") or "hold")
            tuning_adjustments = dict(item.get("tuning_adjustments") or {})
            weight_adjustment = float(tuning_adjustments.get("weight_adjustment", 0.0) or 0.0)
            threshold_adjustment = float(tuning_adjustments.get("threshold_adjustment", 0.0) or 0.0)
            realized_effect = "neutral"
            if tuning_action == "reinforce" and weight_adjustment > 0.0:
                realized_effect = "beneficial"
                beneficial_count += 1
            elif tuning_action == "retune" and threshold_adjustment < 0.0:
                realized_effect = "beneficial"
                beneficial_count += 1
            elif tuning_action == "hold":
                neutral_count += 1
            else:
                realized_effect = "adverse"
                adverse_count += 1

            items.append(
                {
                    **item,
                    "intended_objective": "improve_meta_policy_quality",
                    "realized_effect": realized_effect,
                    "effectiveness_reason_codes": [
                        f"tuning_action:{tuning_action}",
                        f"consumed_effect:{item.get('consumed_effect')}",
                        f"realized_effect:{realized_effect}",
                    ],
                }
            )

        system_effectiveness_action = "observe_meta_policy_effectiveness"
        if adverse_count > 0:
            system_effectiveness_action = "rework_adverse_meta_policy"
        elif beneficial_count > 0:
            system_effectiveness_action = "reinforce_effective_meta_policy"

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
            "policy_effectiveness_summary": payload.get("policy_effectiveness_summary") or {},
            "tuning_summary": payload.get("tuning_summary") or {},
            "persisted_meta_policy_summary": payload.get("persisted_meta_policy_summary") or {},
            "applied_tuning_consumption_summary": payload.get("applied_tuning_consumption_summary") or {},
            "outcome_effectiveness_summary": {
                "family_count": len(items),
                "beneficial_families": beneficial_count,
                "neutral_families": neutral_count,
                "adverse_families": adverse_count,
                "system_effectiveness_action": system_effectiveness_action,
            },
            "as_of": payload.get("as_of"),
        }
