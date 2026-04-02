from __future__ import annotations

import json
from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.services.alpha_strategy_selection_intelligence_service import (
    AlphaStrategySelectionIntelligenceService,
)
from ai_hedge_bot.services.portfolio_intelligence_service import PortfolioIntelligenceService


class SystemLevelLearningFeedbackIntegrationService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.portfolio = PortfolioIntelligenceService()
        self.selection = AlphaStrategySelectionIntelligenceService()

    def _positions_by_symbol(self) -> dict[str, dict[str, Any]]:
        overview = self.portfolio.repo.latest_portfolio_overview()
        return {
            str(row.get("symbol") or ""): row for row in list(overview.get("positions") or [])
        }

    def _portfolio_feedback_by_family(self) -> dict[str, Any]:
        payload = self.portfolio.allocation_outcome_effectiveness_latest()
        positions_by_symbol = self._positions_by_symbol()
        families: dict[str, dict[str, Any]] = {}
        for item in list(payload.get("items") or []):
            symbol = str(item.get("symbol") or "")
            family = str((positions_by_symbol.get(symbol) or {}).get("alpha_family") or "unknown")
            row = families.setdefault(
                family,
                {
                    "alpha_family": family,
                    "beneficial_actions": 0,
                    "neutral_actions": 0,
                    "adverse_actions": 0,
                    "drag_change_usd_total": 0.0,
                    "resolved_weight_change_total": 0.0,
                    "concentration_change_total": 0.0,
                },
            )
            realized_effect = str(item.get("realized_effect") or "neutral")
            if realized_effect == "beneficial":
                row["beneficial_actions"] += 1
            elif realized_effect == "adverse":
                row["adverse_actions"] += 1
            else:
                row["neutral_actions"] += 1
            row["drag_change_usd_total"] += float(item.get("drag_change_usd", 0.0) or 0.0)
            row["resolved_weight_change_total"] += float(item.get("resolved_weight_change", 0.0) or 0.0)
            row["concentration_change_total"] += float(item.get("concentration_change", 0.0) or 0.0)
        return {
            "run_id": payload.get("run_id"),
            "cycle_id": payload.get("cycle_id"),
            "mode": payload.get("mode"),
            "policy_effectiveness_summary": payload.get("policy_effectiveness_summary") or {},
            "items": families,
            "as_of": payload.get("as_of"),
        }

    def _selection_feedback_by_family(self, limit: int) -> dict[str, Any]:
        payload = self.selection.effective_selection_slate_latest(limit=limit)
        families: dict[str, dict[str, Any]] = {}
        for item in list(payload.get("items") or []):
            family = str(item.get("alpha_family") or "unknown")
            row = families.setdefault(
                family,
                {
                    "alpha_family": family,
                    "selected_for_promotion_review": 0,
                    "selected_for_shadow_review": 0,
                    "returned_to_research": 0,
                    "deferred": 0,
                    "selection_score_sum": 0.0,
                    "alpha_count": 0,
                },
            )
            effective_status = str(item.get("effective_status") or "returned_to_research")
            if effective_status in row:
                row[effective_status] += 1
            row["selection_score_sum"] += float(item.get("selection_score", 0.0) or 0.0)
            row["alpha_count"] += 1
        for row in families.values():
            count = max(int(row.get("alpha_count", 0) or 0), 1)
            row["avg_selection_score"] = round(float(row.get("selection_score_sum", 0.0) or 0.0) / count, 6)
            row.pop("selection_score_sum", None)
        return {
            "run_id": payload.get("run_id"),
            "cycle_id": payload.get("cycle_id"),
            "mode": payload.get("mode"),
            "decision_summary": payload.get("decision_summary") or {},
            "control_context": payload.get("control_context") or {},
            "items": families,
            "as_of": payload.get("as_of"),
        }

    def _persisted_transition_feedback_by_family(self) -> dict[str, Any]:
        registry_rows = self.store.fetchall_dict(
            """
            SELECT r.alpha_id, r.alpha_family, r.state, r.source, r.created_at
            FROM alpha_registry r
            WHERE r.rowid IN (
                SELECT MAX(rowid)
                FROM alpha_registry
                GROUP BY alpha_id
            )
            AND r.source LIKE 'research_promotion_intelligence_%'
            ORDER BY r.created_at DESC, r.alpha_id ASC
            """
        )
        families: dict[str, dict[str, Any]] = {}
        for row in registry_rows:
            family = str(row.get("alpha_family") or "unknown")
            state = str(row.get("state") or "candidate")
            agg = families.setdefault(
                family,
                {
                    "alpha_family": family,
                    "promoted_states": 0,
                    "shadow_states": 0,
                    "retired_states": 0,
                    "rejected_states": 0,
                    "candidate_states": 0,
                    "transition_count": 0,
                },
            )
            agg["transition_count"] += 1
            if state == "promoted":
                agg["promoted_states"] += 1
            elif state == "shadow":
                agg["shadow_states"] += 1
            elif state == "retired":
                agg["retired_states"] += 1
            elif state == "rejected":
                agg["rejected_states"] += 1
            else:
                agg["candidate_states"] += 1
        as_of = registry_rows[0].get("created_at") if registry_rows else None
        return {
            "items": families,
            "transition_summary": {
                "family_count": len(families),
                "transition_count": sum(int(item.get("transition_count", 0) or 0) for item in families.values()),
            },
            "as_of": as_of,
        }

    @staticmethod
    def _coherent(a: Any, b: Any) -> bool:
        return a in {None, ""} or b in {None, ""} or a == b

    def latest(self, limit: int = 20) -> dict[str, Any]:
        portfolio_feedback = self._portfolio_feedback_by_family()
        selection_feedback = self._selection_feedback_by_family(limit)
        transition_feedback = self._persisted_transition_feedback_by_family()

        run_id = portfolio_feedback.get("run_id") or selection_feedback.get("run_id")
        cycle_id = portfolio_feedback.get("cycle_id") or selection_feedback.get("cycle_id")
        mode = portfolio_feedback.get("mode") or selection_feedback.get("mode")
        control_context = dict(selection_feedback.get("control_context") or {})
        global_guard_decision = str(control_context.get("global_guard_decision") or "continue")

        families = sorted(
            set(dict(portfolio_feedback.get("items") or {}).keys())
            | set(dict(selection_feedback.get("items") or {}).keys())
            | set(dict(transition_feedback.get("items") or {}).keys())
        )

        items: list[dict[str, Any]] = []
        reinforce_count = 0
        caution_count = 0
        rebalance_count = 0
        observe_count = 0
        for family in families:
            portfolio_item = dict((portfolio_feedback.get("items") or {}).get(family) or {})
            selection_item = dict((selection_feedback.get("items") or {}).get(family) or {})
            transition_item = dict((transition_feedback.get("items") or {}).get(family) or {})

            beneficial = int(portfolio_item.get("beneficial_actions", 0) or 0)
            neutral = int(portfolio_item.get("neutral_actions", 0) or 0)
            adverse = int(portfolio_item.get("adverse_actions", 0) or 0)
            promotion_pressure = int(selection_item.get("selected_for_promotion_review", 0) or 0) + int(
                selection_item.get("selected_for_shadow_review", 0) or 0
            )
            research_pressure = int(selection_item.get("returned_to_research", 0) or 0) + int(
                selection_item.get("deferred", 0) or 0
            )
            governed_positive = int(transition_item.get("promoted_states", 0) or 0) + int(
                transition_item.get("shadow_states", 0) or 0
            )
            governed_negative = int(transition_item.get("retired_states", 0) or 0) + int(
                transition_item.get("rejected_states", 0) or 0
            )

            learning_action = "observe"
            reason_codes: list[str] = []
            if adverse > 0:
                reason_codes.append("adverse_realized_feedback_present")
            if beneficial > 0:
                reason_codes.append("beneficial_realized_feedback_present")
            if promotion_pressure > 0:
                reason_codes.append("selection_pressure_present")
            if research_pressure > 0:
                reason_codes.append("research_pressure_present")
            if governed_positive > 0:
                reason_codes.append("positive_governed_transition_present")
            if governed_negative > 0:
                reason_codes.append("negative_governed_transition_present")

            if global_guard_decision in {"halt", "pause"} and adverse > 0:
                learning_action = "caution"
                reason_codes.append(f"global_guard_{global_guard_decision}")
            elif beneficial > 0 and adverse > 0:
                learning_action = "rebalance"
                reason_codes.append("mixed_feedback_requires_rebalance")
            elif adverse > beneficial or governed_negative > 0:
                learning_action = "caution"
                reason_codes.append("negative_feedback_dominant")
            elif beneficial > 0 and (promotion_pressure > 0 or governed_positive > 0):
                learning_action = "reinforce"
                reason_codes.append("positive_feedback_supported_across_layers")
            else:
                learning_action = "observe"
                reason_codes.append("collect_more_cross_layer_feedback")

            if learning_action == "reinforce":
                reinforce_count += 1
            elif learning_action == "caution":
                caution_count += 1
            elif learning_action == "rebalance":
                rebalance_count += 1
            else:
                observe_count += 1

            items.append(
                {
                    "alpha_family": family,
                    "portfolio_feedback": {
                        "beneficial_actions": beneficial,
                        "neutral_actions": neutral,
                        "adverse_actions": adverse,
                        "drag_change_usd_total": round(float(portfolio_item.get("drag_change_usd_total", 0.0) or 0.0), 6),
                        "resolved_weight_change_total": round(float(portfolio_item.get("resolved_weight_change_total", 0.0) or 0.0), 6),
                        "concentration_change_total": round(float(portfolio_item.get("concentration_change_total", 0.0) or 0.0), 6),
                    },
                    "selection_feedback": {
                        "selected_for_promotion_review": int(selection_item.get("selected_for_promotion_review", 0) or 0),
                        "selected_for_shadow_review": int(selection_item.get("selected_for_shadow_review", 0) or 0),
                        "returned_to_research": int(selection_item.get("returned_to_research", 0) or 0),
                        "deferred": int(selection_item.get("deferred", 0) or 0),
                        "avg_selection_score": float(selection_item.get("avg_selection_score", 0.0) or 0.0),
                    },
                    "governed_transition_feedback": {
                        "promoted_states": int(transition_item.get("promoted_states", 0) or 0),
                        "shadow_states": int(transition_item.get("shadow_states", 0) or 0),
                        "retired_states": int(transition_item.get("retired_states", 0) or 0),
                        "rejected_states": int(transition_item.get("rejected_states", 0) or 0),
                        "candidate_states": int(transition_item.get("candidate_states", 0) or 0),
                    },
                    "learning_action": learning_action,
                    "learning_reason_codes": reason_codes,
                }
            )

        run_id_coherent = self._coherent(portfolio_feedback.get("run_id"), selection_feedback.get("run_id"))
        cycle_id_coherent = self._coherent(portfolio_feedback.get("cycle_id"), selection_feedback.get("cycle_id"))
        mode_coherent = self._coherent(portfolio_feedback.get("mode"), selection_feedback.get("mode"))
        coherence = run_id_coherent and cycle_id_coherent and mode_coherent

        system_learning_action = "observe_and_collect_more_feedback"
        if global_guard_decision in {"halt", "pause"} and caution_count > 0:
            system_learning_action = "stabilize_before_expansion"
        elif caution_count > 0:
            system_learning_action = "contain_negative_feedback"
        elif rebalance_count > 0:
            system_learning_action = "rebalance_mixed_feedback"
        elif reinforce_count > 0:
            system_learning_action = "reinforce_positive_families"

        return {
            "status": "ok",
            "run_id": run_id,
            "cycle_id": cycle_id,
            "mode": mode,
            "items": items,
            "cross_layer_coherence": {
                "run_id_coherent": run_id_coherent,
                "cycle_id_coherent": cycle_id_coherent,
                "mode_coherent": mode_coherent,
                "coherent": coherence,
            },
            "source_packets": {
                "portfolio": "PI-05",
                "selection": "ASI-05",
                "research_promotion_persisted_state": "RPI-06",
            },
            "feedback_summary": {
                "family_count": len(items),
                "reinforce_families": reinforce_count,
                "caution_families": caution_count,
                "rebalance_families": rebalance_count,
                "observe_families": observe_count,
                "system_learning_action": system_learning_action,
            },
            "control_context": control_context,
            "portfolio_effectiveness_summary": portfolio_feedback.get("policy_effectiveness_summary") or {},
            "selection_summary": selection_feedback.get("decision_summary") or {},
            "governed_transition_summary": transition_feedback.get("transition_summary") or {},
            "as_of": portfolio_feedback.get("as_of") or selection_feedback.get("as_of") or transition_feedback.get("as_of"),
        }

    def policy_updates_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.latest(limit=limit)
        items: list[dict[str, Any]] = []
        reinforce_count = 0
        caution_count = 0
        rebalance_count = 0
        observe_count = 0

        for item in list(payload.get("items") or []):
            learning_action = str(item.get("learning_action") or "observe")
            selection_score_adjustment = 0.0
            capital_multiplier_adjustment = 1.0
            review_pressure = "normal"
            runtime_caution = "normal"
            update_reason_codes = list(item.get("learning_reason_codes") or [])

            if learning_action == "reinforce":
                selection_score_adjustment = 0.08
                capital_multiplier_adjustment = 1.1
                review_pressure = "increase"
                runtime_caution = "normal"
                reinforce_count += 1
            elif learning_action == "caution":
                selection_score_adjustment = -0.12
                capital_multiplier_adjustment = 0.75
                review_pressure = "decrease"
                runtime_caution = "high"
                caution_count += 1
            elif learning_action == "rebalance":
                selection_score_adjustment = -0.03
                capital_multiplier_adjustment = 0.95
                review_pressure = "rebalance"
                runtime_caution = "elevated"
                rebalance_count += 1
            else:
                review_pressure = "hold"
                runtime_caution = "normal"
                observe_count += 1

            items.append(
                {
                    **item,
                    "selection_score_adjustment": selection_score_adjustment,
                    "capital_multiplier_adjustment": capital_multiplier_adjustment,
                    "review_pressure": review_pressure,
                    "runtime_caution": runtime_caution,
                    "policy_update_reason_codes": update_reason_codes,
                }
            )

        system_policy_action = "hold_current_policy"
        if caution_count > 0:
            system_policy_action = "tighten_policy_for_negative_families"
        elif rebalance_count > 0:
            system_policy_action = "rebalance_policy_mixed_families"
        elif reinforce_count > 0:
            system_policy_action = "increase_policy_support_for_positive_families"

        return {
            "status": "ok",
            "run_id": payload.get("run_id"),
            "cycle_id": payload.get("cycle_id"),
            "mode": payload.get("mode"),
            "items": items,
            "cross_layer_coherence": payload.get("cross_layer_coherence") or {},
            "source_packets": payload.get("source_packets") or {},
            "feedback_summary": payload.get("feedback_summary") or {},
            "policy_update_summary": {
                "family_count": len(items),
                "reinforce_updates": reinforce_count,
                "caution_updates": caution_count,
                "rebalance_updates": rebalance_count,
                "observe_updates": observe_count,
                "system_policy_action": system_policy_action,
            },
            "control_context": payload.get("control_context") or {},
            "as_of": payload.get("as_of"),
        }

    def persisted_policy_state_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.policy_updates_latest(limit=limit)
        created_at = utc_now_iso()
        items: list[dict[str, Any]] = []

        for item in list(payload.get("items") or []):
            family = str(item.get("alpha_family") or "unknown")
            previous_state = self.store.fetchone_dict(
                """
                SELECT *
                FROM audit_logs
                WHERE category='system_learning_policy_state'
                  AND actor=?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                [family],
            ) or {}
            state_id = new_cycle_id()
            applied_state = {
                "audit_id": state_id,
                "created_at": created_at,
                "category": "system_learning_policy_state",
                "event_type": "persist_learning_policy_state",
                "run_id": payload.get("run_id"),
                "payload_json": self.store.to_json(
                    {
                        "alpha_family": family,
                        "run_id": payload.get("run_id"),
                        "cycle_id": payload.get("cycle_id"),
                        "mode": payload.get("mode"),
                        "applied_learning_action": item.get("learning_action"),
                        "applied_selection_score_adjustment": item.get("selection_score_adjustment"),
                        "applied_capital_multiplier": item.get("capital_multiplier_adjustment"),
                        "applied_review_pressure": item.get("review_pressure"),
                        "applied_runtime_caution": item.get("runtime_caution"),
                        "policy_source_packet": "SLLFI-02",
                    }
                ),
                "actor": family,
            }
            self.store.append("audit_logs", applied_state)
            items.append(
                {
                    **item,
                    "policy_state_id": state_id,
                    "previous_policy_state_id": previous_state.get("audit_id"),
                    "applied_selection_score_adjustment": item.get("selection_score_adjustment"),
                    "applied_capital_multiplier": item.get("capital_multiplier_adjustment"),
                    "applied_review_pressure": item.get("review_pressure"),
                    "applied_runtime_caution": item.get("runtime_caution"),
                    "policy_transition_timestamp": created_at,
                    "policy_source_packet": "SLLFI-02",
                }
            )

        return {
            "status": "ok",
            "run_id": payload.get("run_id"),
            "cycle_id": payload.get("cycle_id"),
            "mode": payload.get("mode"),
            "items": items,
            "cross_layer_coherence": payload.get("cross_layer_coherence") or {},
            "source_packets": payload.get("source_packets") or {},
            "feedback_summary": payload.get("feedback_summary") or {},
            "policy_update_summary": payload.get("policy_update_summary") or {},
            "persisted_policy_state_summary": {
                "family_count": len(items),
                "persisted_states": len(items),
                "system_policy_state_action": "persist_next_cycle_learning_policy",
            },
            "control_context": payload.get("control_context") or {},
            "as_of": created_at,
        }

    def resolved_overrides_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.persisted_policy_state_latest(limit=limit)
        items: list[dict[str, Any]] = []
        expand_count = 0
        constrain_count = 0
        mixed_count = 0
        neutral_count = 0

        for item in list(payload.get("items") or []):
            learning_action = str(item.get("learning_action") or "observe")
            selection_adj = float(item.get("applied_selection_score_adjustment", 0.0) or 0.0)
            capital_mult = float(item.get("applied_capital_multiplier", 1.0) or 1.0)
            review_pressure = str(item.get("applied_review_pressure") or "hold")
            runtime_caution = str(item.get("applied_runtime_caution") or "normal")

            override_state = "neutral"
            if learning_action == "reinforce":
                override_state = "expand"
                expand_count += 1
            elif learning_action == "caution":
                override_state = "constrain"
                constrain_count += 1
            elif learning_action == "rebalance":
                override_state = "mixed"
                mixed_count += 1
            else:
                neutral_count += 1

            selection_override = {
                "score_adjustment": selection_adj,
                "selection_bias": "favor" if selection_adj > 0 else "penalize" if selection_adj < 0 else "neutral",
            }
            capital_override = {
                "capital_multiplier": capital_mult,
                "capital_bias": "expand" if capital_mult > 1.0 else "constrain" if capital_mult < 1.0 else "hold",
            }
            review_override = {
                "review_pressure": review_pressure,
            }
            runtime_override = {
                "runtime_caution": runtime_caution,
            }

            items.append(
                {
                    **item,
                    "override_state": override_state,
                    "selection_override": selection_override,
                    "capital_override": capital_override,
                    "review_override": review_override,
                    "runtime_override": runtime_override,
                }
            )

        system_override_action = "hold_overrides"
        if constrain_count > 0:
            system_override_action = "apply_constraining_overrides"
        elif mixed_count > 0:
            system_override_action = "apply_mixed_overrides"
        elif expand_count > 0:
            system_override_action = "apply_expansion_overrides"

        return {
            "status": "ok",
            "run_id": payload.get("run_id"),
            "cycle_id": payload.get("cycle_id"),
            "mode": payload.get("mode"),
            "items": items,
            "cross_layer_coherence": payload.get("cross_layer_coherence") or {},
            "source_packets": payload.get("source_packets") or {},
            "feedback_summary": payload.get("feedback_summary") or {},
            "policy_update_summary": payload.get("policy_update_summary") or {},
            "persisted_policy_state_summary": payload.get("persisted_policy_state_summary") or {},
            "resolved_override_summary": {
                "family_count": len(items),
                "expand_overrides": expand_count,
                "constrain_overrides": constrain_count,
                "mixed_overrides": mixed_count,
                "neutral_overrides": neutral_count,
                "system_override_action": system_override_action,
            },
            "control_context": payload.get("control_context") or {},
            "as_of": payload.get("as_of"),
        }

    def applied_override_consumption_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.resolved_overrides_latest(limit=limit)
        consumed_run_id = f"{payload.get('run_id') or 'unknown'}:next"
        consumed_cycle_id = f"{payload.get('cycle_id') or 'unknown'}:next"
        items: list[dict[str, Any]] = []
        consumed_count = 0
        constrained_count = 0
        expanded_count = 0
        mixed_count = 0

        for item in list(payload.get("items") or []):
            override_state = str(item.get("override_state") or "neutral")
            selection_override = dict(item.get("selection_override") or {})
            capital_override = dict(item.get("capital_override") or {})
            review_override = dict(item.get("review_override") or {})
            runtime_override = dict(item.get("runtime_override") or {})

            selection_consumed = {
                "consumed": True,
                "consumed_run_id": consumed_run_id,
                "consumed_cycle_id": consumed_cycle_id,
                "applied_score_adjustment": selection_override.get("score_adjustment", 0.0),
                "applied_selection_bias": selection_override.get("selection_bias", "neutral"),
            }
            capital_consumed = {
                "consumed": True,
                "consumed_run_id": consumed_run_id,
                "consumed_cycle_id": consumed_cycle_id,
                "applied_capital_multiplier": capital_override.get("capital_multiplier", 1.0),
                "applied_capital_bias": capital_override.get("capital_bias", "hold"),
            }
            review_consumed = {
                "consumed": True,
                "consumed_run_id": consumed_run_id,
                "consumed_cycle_id": consumed_cycle_id,
                "applied_review_pressure": review_override.get("review_pressure", "hold"),
            }
            runtime_consumed = {
                "consumed": True,
                "consumed_run_id": consumed_run_id,
                "consumed_cycle_id": consumed_cycle_id,
                "applied_runtime_caution": runtime_override.get("runtime_caution", "normal"),
            }

            consumed_effect = "neutral_consumption"
            if override_state == "expand":
                consumed_effect = "expansion_applied"
                expanded_count += 1
            elif override_state == "constrain":
                consumed_effect = "constraint_applied"
                constrained_count += 1
            elif override_state == "mixed":
                consumed_effect = "mixed_override_applied"
                mixed_count += 1
            consumed_count += 1

            items.append(
                {
                    **item,
                    "consumed_run_id": consumed_run_id,
                    "consumed_cycle_id": consumed_cycle_id,
                    "selection_consumption": selection_consumed,
                    "capital_consumption": capital_consumed,
                    "review_consumption": review_consumed,
                    "runtime_consumption": runtime_consumed,
                    "consumed_effect": consumed_effect,
                }
            )

        system_consumption_action = "apply_neutral_overrides"
        if constrained_count > 0:
            system_consumption_action = "apply_constrained_next_cycle"
        elif mixed_count > 0:
            system_consumption_action = "apply_mixed_next_cycle"
        elif expanded_count > 0:
            system_consumption_action = "apply_expanded_next_cycle"

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
            "feedback_summary": payload.get("feedback_summary") or {},
            "policy_update_summary": payload.get("policy_update_summary") or {},
            "persisted_policy_state_summary": payload.get("persisted_policy_state_summary") or {},
            "resolved_override_summary": payload.get("resolved_override_summary") or {},
            "applied_consumption_summary": {
                "family_count": len(items),
                "consumed_overrides": consumed_count,
                "expanded_consumptions": expanded_count,
                "constrained_consumptions": constrained_count,
                "mixed_consumptions": mixed_count,
                "system_consumption_action": system_consumption_action,
            },
            "control_context": payload.get("control_context") or {},
            "as_of": payload.get("as_of"),
        }
