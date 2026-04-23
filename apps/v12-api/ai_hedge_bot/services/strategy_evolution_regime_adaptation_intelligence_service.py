from __future__ import annotations

from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.services.alpha_strategy_selection_intelligence_service import (
    AlphaStrategySelectionIntelligenceService,
)
from ai_hedge_bot.services.live_capital_control_adaptive_runtime_allocation_service import (
    LiveCapitalControlAdaptiveRuntimeAllocationService,
)
from ai_hedge_bot.services.meta_portfolio_intelligence_cross_strategy_capital_allocation_service import (
    MetaPortfolioIntelligenceCrossStrategyCapitalAllocationService,
)
from ai_hedge_bot.services.research_promotion_intelligence_service import (
    ResearchPromotionIntelligenceService,
)


class StrategyEvolutionRegimeAdaptationIntelligenceService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.alpha_selection = AlphaStrategySelectionIntelligenceService()
        self.live_capital_control = LiveCapitalControlAdaptiveRuntimeAllocationService()
        self.meta_portfolio = MetaPortfolioIntelligenceCrossStrategyCapitalAllocationService()
        self.research_promotion = ResearchPromotionIntelligenceService()

    @staticmethod
    def _family_regime_state(
        control_state: str,
        live_effect: str,
        meta_effect: str,
        promotion_pressure: str,
    ) -> tuple[str, float]:
        normalized_control = str(control_state or "live").lower()
        normalized_live_effect = str(live_effect or "neutral").lower()
        normalized_meta_effect = str(meta_effect or "neutral").lower()
        normalized_pressure = str(promotion_pressure or "stable").lower()

        if normalized_control == "frozen" or (
            normalized_live_effect == "adverse" and normalized_meta_effect == "adverse"
        ):
            return "risk_off", 0.88
        if normalized_control in {"reduced", "degraded"} or "transition" in normalized_pressure:
            return "transition", 0.72
        if (
            normalized_control == "live"
            and normalized_live_effect == "beneficial"
            and normalized_meta_effect == "beneficial"
        ):
            return "risk_on", 0.83
        return "balanced", 0.61

    @staticmethod
    def _system_action(current_regime: str) -> str:
        normalized = str(current_regime or "balanced").lower()
        if normalized == "risk_off":
            return "gate_fragile_strategies"
        if normalized == "transition":
            return "observe_regime_shift_and_prepare_gating"
        if normalized == "risk_on":
            return "allow_selective_strategy_expansion"
        return "maintain_current_strategy_posture"

    def latest(self, limit: int = 20) -> dict[str, Any]:
        live_capital = self.live_capital_control.control_effectiveness_latest(limit=limit)
        meta_portfolio = self.meta_portfolio.efficiency_latest(limit=limit)
        research = self.research_promotion.persisted_governed_state_transitions_latest(limit=limit)

        live_by_family = {
            str(item.get("alpha_family") or ""): item for item in list(live_capital.get("items") or [])
        }
        meta_by_family = {
            str(item.get("alpha_family") or ""): item for item in list(meta_portfolio.get("items") or [])
        }

        research_items = list(research.get("items") or [])
        promotion_pressure_by_family: dict[str, str] = {}
        transition_counts_by_family: dict[str, int] = {}
        for item in research_items:
            family = str(item.get("alpha_family") or "unknown")
            transition_counts_by_family[family] = transition_counts_by_family.get(family, 0) + 1
            new_state = str(item.get("new_governed_state") or "candidate")
            pressure = "stable"
            if new_state in {"retired", "rejected"}:
                pressure = "transition_pressure"
            elif new_state in {"promoted", "shadow"}:
                pressure = "expansion_pressure"
            promotion_pressure_by_family[family] = pressure

        families = sorted(
            {
                family
                for family in list(live_by_family.keys()) + list(meta_by_family.keys()) + list(promotion_pressure_by_family.keys())
                if family
            }
        )

        items: list[dict[str, Any]] = []
        risk_on_count = 0
        balanced_count = 0
        transition_count = 0
        risk_off_count = 0

        for family in families:
            live_item = dict(live_by_family.get(family) or {})
            meta_item = dict(meta_by_family.get(family) or {})
            control_state = str(live_item.get("control_state") or live_item.get("current_mode") or "live")
            live_effect = str(live_item.get("realized_effect") or "neutral")
            meta_effect = str(meta_item.get("realized_effect") or "neutral")
            promotion_pressure = str(promotion_pressure_by_family.get(family) or "stable")
            family_regime_state, regime_confidence = self._family_regime_state(
                control_state=control_state,
                live_effect=live_effect,
                meta_effect=meta_effect,
                promotion_pressure=promotion_pressure,
            )

            if family_regime_state == "risk_on":
                risk_on_count += 1
            elif family_regime_state == "risk_off":
                risk_off_count += 1
            elif family_regime_state == "transition":
                transition_count += 1
            else:
                balanced_count += 1

            items.append(
                {
                    "alpha_family": family,
                    "control_state": control_state,
                    "live_capital_effect": live_effect,
                    "meta_portfolio_effect": meta_effect,
                    "promotion_pressure": promotion_pressure,
                    "family_regime_state": family_regime_state,
                    "regime_confidence": round(regime_confidence, 6),
                    "supporting_signals": {
                        "transition_event_count": transition_counts_by_family.get(family, 0),
                        "live_capital_action": live_item.get("live_control_action"),
                        "meta_portfolio_action": meta_item.get("allocation_action"),
                    },
                }
            )

        current_regime = "balanced"
        if risk_off_count > 0:
            current_regime = "risk_off"
        elif transition_count > 0:
            current_regime = "transition"
        elif risk_on_count > 0 and balanced_count == 0:
            current_regime = "risk_on"

        total_families = max(len(items), 1)
        dominant_count = max(risk_on_count, balanced_count, transition_count, risk_off_count)
        top_level_confidence = round(dominant_count / total_families, 6)

        return {
            "status": "ok",
            "run_id": live_capital.get("run_id") or meta_portfolio.get("run_id") or research.get("run_id"),
            "cycle_id": live_capital.get("cycle_id") or meta_portfolio.get("cycle_id") or research.get("cycle_id"),
            "mode": live_capital.get("mode") or meta_portfolio.get("mode") or research.get("mode"),
            "consumed_run_id": live_capital.get("consumed_run_id") or meta_portfolio.get("consumed_run_id"),
            "consumed_cycle_id": live_capital.get("consumed_cycle_id") or meta_portfolio.get("consumed_cycle_id"),
            "items": items,
            "current_regime": current_regime,
            "regime_confidence": top_level_confidence,
            "supporting_signals": {
                "risk_on_families": risk_on_count,
                "balanced_families": balanced_count,
                "transition_families": transition_count,
                "risk_off_families": risk_off_count,
                "promotion_transition_events": len(research_items),
            },
            "system_regime_action": self._system_action(current_regime),
            "source_packets": {
                "live_capital_control": "LCC-05",
                "meta_portfolio_intelligence": "MPI-05",
                "research_promotion_intelligence": "RPI-06",
            },
            "regime_state_summary": {
                "family_count": len(items),
                "risk_on_families": risk_on_count,
                "balanced_families": balanced_count,
                "transition_families": transition_count,
                "risk_off_families": risk_off_count,
                "current_regime": current_regime,
                "system_regime_action": self._system_action(current_regime),
            },
            "as_of": live_capital.get("as_of") or meta_portfolio.get("as_of") or research.get("as_of"),
        }

    def strategy_regime_compatibility_latest(self, limit: int = 20) -> dict[str, Any]:
        regime_state = self.latest(limit=limit)
        selection = self.alpha_selection.effective_selection_slate_latest(limit=limit)

        selection_items = list(selection.get("items") or [])
        selection_by_family: dict[str, list[dict[str, Any]]] = {}
        for item in selection_items:
            family = str(item.get("alpha_family") or "unknown")
            selection_by_family.setdefault(family, []).append(item)

        items: list[dict[str, Any]] = []
        compatible_count = 0
        watch_count = 0
        incompatible_count = 0

        for item in list(regime_state.get("items") or []):
            family = str(item.get("alpha_family") or "unknown")
            family_selection = selection_by_family.get(family) or []
            avg_selection_score = 0.0
            if family_selection:
                avg_selection_score = sum(
                    float(candidate.get("selection_score", 0.0) or 0.0) for candidate in family_selection
                ) / len(family_selection)

            family_regime_state = str(item.get("family_regime_state") or "balanced")
            promotion_pressure = str(item.get("promotion_pressure") or "stable")
            control_state = str(item.get("control_state") or "live")

            compatibility_status = "watch"
            compatibility_score = 0.55
            recommended_posture = "observe"
            reason_codes: list[str] = []

            if family_regime_state == "risk_off":
                compatibility_status = "incompatible"
                compatibility_score = 0.18
                recommended_posture = "gate"
                reason_codes.append("risk_off_regime_blocks_family")
                incompatible_count += 1
            elif family_regime_state == "transition" or promotion_pressure == "transition_pressure":
                compatibility_status = "watch"
                compatibility_score = 0.44
                recommended_posture = "shadow_or_reduce"
                reason_codes.append("family_is_in_regime_transition")
                watch_count += 1
            elif family_regime_state == "risk_on" and avg_selection_score >= 0.6 and control_state == "live":
                compatibility_status = "compatible"
                compatibility_score = 0.84
                recommended_posture = "allow"
                reason_codes.append("family_matches_supportive_regime")
                compatible_count += 1
            else:
                compatibility_status = "watch"
                compatibility_score = 0.61 if avg_selection_score >= 0.5 else 0.49
                recommended_posture = "observe"
                reason_codes.append("family_regime_fit_is_not_decisive")
                watch_count += 1

            reason_codes.extend(
                [
                    f"family_regime_state:{family_regime_state}",
                    f"avg_selection_score:{round(avg_selection_score, 6)}",
                    f"control_state:{control_state}",
                ]
            )

            items.append(
                {
                    **item,
                    "avg_selection_score": round(avg_selection_score, 6),
                    "compatibility_status": compatibility_status,
                    "compatibility_score": round(compatibility_score, 6),
                    "recommended_posture": recommended_posture,
                    "compatibility_reason_codes": reason_codes,
                }
            )

        system_action = "observe_strategy_regime_compatibility"
        if incompatible_count > 0:
            system_action = "identify_regime_incompatible_families"
        elif compatible_count > 0 and watch_count == 0:
            system_action = "reinforce_regime_compatible_families"

        return {
            "status": "ok",
            "run_id": regime_state.get("run_id"),
            "cycle_id": regime_state.get("cycle_id"),
            "mode": regime_state.get("mode"),
            "consumed_run_id": regime_state.get("consumed_run_id"),
            "consumed_cycle_id": regime_state.get("consumed_cycle_id"),
            "items": items,
            "current_regime": regime_state.get("current_regime"),
            "regime_confidence": regime_state.get("regime_confidence"),
            "supporting_signals": regime_state.get("supporting_signals") or {},
            "system_regime_action": regime_state.get("system_regime_action"),
            "source_packets": {
                **(regime_state.get("source_packets") or {}),
                "alpha_strategy_selection_intelligence": "ASI-05",
            },
            "regime_state_summary": regime_state.get("regime_state_summary") or {},
            "strategy_regime_compatibility_summary": {
                "family_count": len(items),
                "compatible_families": compatible_count,
                "watch_families": watch_count,
                "incompatible_families": incompatible_count,
                "system_strategy_regime_action": system_action,
            },
            "as_of": regime_state.get("as_of"),
        }

    def strategy_gating_decision_latest(self, limit: int = 20) -> dict[str, Any]:
        compatibility = self.strategy_regime_compatibility_latest(limit=limit)
        items: list[dict[str, Any]] = []
        allow_count = 0
        shadow_count = 0
        gate_count = 0
        retire_count = 0

        for item in list(compatibility.get("items") or []):
            compatibility_status = str(item.get("compatibility_status") or "watch")
            recommended_posture = str(item.get("recommended_posture") or "observe")
            promotion_pressure = str(item.get("promotion_pressure") or "stable")
            family_regime_state = str(item.get("family_regime_state") or "balanced")
            compatibility_score = float(item.get("compatibility_score", 0.0) or 0.0)

            gating_decision = "shadow"
            gating_reason = "family_requires_more_regime_evidence"

            if compatibility_status == "incompatible" and promotion_pressure == "transition_pressure":
                gating_decision = "retire"
                gating_reason = "regime_mismatch_is_severe_and_persistent"
                retire_count += 1
            elif compatibility_status == "incompatible":
                gating_decision = "gate"
                gating_reason = "family_is_not_compatible_with_current_regime"
                gate_count += 1
            elif compatibility_status == "compatible" and recommended_posture == "allow" and compatibility_score >= 0.8:
                gating_decision = "allow"
                gating_reason = "family_is_compatible_with_current_regime"
                allow_count += 1
            else:
                gating_decision = "shadow"
                gating_reason = "family_should_remain_under_observation"
                shadow_count += 1

            items.append(
                {
                    **item,
                    "strategy_gating_decision": gating_decision,
                    "gating_reason": gating_reason,
                    "gating_reason_codes": [
                        f"compatibility_status:{compatibility_status}",
                        f"recommended_posture:{recommended_posture}",
                        f"family_regime_state:{family_regime_state}",
                        f"compatibility_score:{round(compatibility_score, 6)}",
                    ],
                }
            )

        system_action = "keep_strategies_under_regime_observation"
        if retire_count > 0:
            system_action = "retire_regime_broken_families"
        elif gate_count > 0:
            system_action = "gate_regime_incompatible_families"
        elif allow_count > 0 and shadow_count == 0:
            system_action = "allow_regime_aligned_families"

        return {
            "status": "ok",
            "run_id": compatibility.get("run_id"),
            "cycle_id": compatibility.get("cycle_id"),
            "mode": compatibility.get("mode"),
            "consumed_run_id": compatibility.get("consumed_run_id"),
            "consumed_cycle_id": compatibility.get("consumed_cycle_id"),
            "items": items,
            "current_regime": compatibility.get("current_regime"),
            "regime_confidence": compatibility.get("regime_confidence"),
            "supporting_signals": compatibility.get("supporting_signals") or {},
            "system_regime_action": compatibility.get("system_regime_action"),
            "source_packets": compatibility.get("source_packets") or {},
            "regime_state_summary": compatibility.get("regime_state_summary") or {},
            "strategy_regime_compatibility_summary": compatibility.get("strategy_regime_compatibility_summary") or {},
            "strategy_gating_decision_summary": {
                "family_count": len(items),
                "allow_families": allow_count,
                "shadow_families": shadow_count,
                "gate_families": gate_count,
                "retire_families": retire_count,
                "system_strategy_gating_action": system_action,
            },
            "as_of": compatibility.get("as_of"),
        }

    def regime_transition_detection_latest(self, limit: int = 20) -> dict[str, Any]:
        gating = self.strategy_gating_decision_latest(limit=limit)
        created_at = utc_now_iso()
        items: list[dict[str, Any]] = []
        stable_count = 0
        emerging_count = 0
        confirmed_count = 0

        for item in list(gating.get("items") or []):
            family = str(item.get("alpha_family") or "unknown")
            previous_detection = self.store.fetchone_dict(
                """
                SELECT *
                FROM audit_logs
                WHERE category='strategy_regime_transition_detection'
                  AND actor=?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                [family],
            ) or {}
            previous_payload = self.store.parse_json(previous_detection.get("payload_json")) if previous_detection else {}
            previous_regime_state = str(previous_payload.get("family_regime_state") or "unknown")
            previous_gating_decision = str(previous_payload.get("strategy_gating_decision") or "unknown")

            family_regime_state = str(item.get("family_regime_state") or "balanced")
            gating_decision = str(item.get("strategy_gating_decision") or "shadow")

            transition_detected = False
            detection_strength = "stable"
            transition_reason = "regime_posture_unchanged"

            if previous_regime_state in {"unknown", ""}:
                if family_regime_state in {"transition", "risk_off"} or gating_decision in {"gate", "retire"}:
                    transition_detected = True
                    detection_strength = "emerging"
                    transition_reason = "first_material_regime_shift_signal"
                    emerging_count += 1
                else:
                    stable_count += 1
            elif previous_regime_state != family_regime_state or previous_gating_decision != gating_decision:
                transition_detected = True
                if family_regime_state == "risk_off" or gating_decision in {"gate", "retire"}:
                    detection_strength = "confirmed"
                    transition_reason = "regime_shift_is_now_actionable"
                    confirmed_count += 1
                else:
                    detection_strength = "emerging"
                    transition_reason = "regime_shift_is_starting_to_form"
                    emerging_count += 1
            else:
                stable_count += 1

            transition_id = new_cycle_id()
            self.store.append(
                "audit_logs",
                {
                    "audit_id": transition_id,
                    "created_at": created_at,
                    "category": "strategy_regime_transition_detection",
                    "event_type": "detect_strategy_regime_transition",
                    "run_id": gating.get("run_id"),
                    "payload_json": self.store.to_json(
                        {
                            "alpha_family": family,
                            "family_regime_state": family_regime_state,
                            "strategy_gating_decision": gating_decision,
                            "transition_detected": transition_detected,
                            "detection_strength": detection_strength,
                            "transition_source_packet": "SERI-03",
                        }
                    ),
                    "actor": family,
                },
            )

            items.append(
                {
                    **item,
                    "regime_transition_detection": {
                        "transition_detected": transition_detected,
                        "detection_strength": detection_strength,
                        "previous_family_regime_state": previous_regime_state,
                        "previous_strategy_gating_decision": previous_gating_decision,
                        "transition_reason": transition_reason,
                        "transition_detection_id": transition_id,
                    },
                }
            )

        system_action = "maintain_current_regime_interpretation"
        if confirmed_count > 0:
            system_action = "confirm_regime_transition_and_prepare_survival_actions"
        elif emerging_count > 0:
            system_action = "monitor_emerging_regime_transition"

        return {
            "status": "ok",
            "run_id": gating.get("run_id"),
            "cycle_id": gating.get("cycle_id"),
            "mode": gating.get("mode"),
            "consumed_run_id": gating.get("consumed_run_id"),
            "consumed_cycle_id": gating.get("consumed_cycle_id"),
            "items": items,
            "current_regime": gating.get("current_regime"),
            "regime_confidence": gating.get("regime_confidence"),
            "supporting_signals": gating.get("supporting_signals") or {},
            "system_regime_action": gating.get("system_regime_action"),
            "source_packets": gating.get("source_packets") or {},
            "regime_state_summary": gating.get("regime_state_summary") or {},
            "strategy_regime_compatibility_summary": gating.get("strategy_regime_compatibility_summary") or {},
            "strategy_gating_decision_summary": gating.get("strategy_gating_decision_summary") or {},
            "regime_transition_detection_summary": {
                "family_count": len(items),
                "stable_families": stable_count,
                "emerging_transition_families": emerging_count,
                "confirmed_transition_families": confirmed_count,
                "system_regime_transition_action": system_action,
            },
            "as_of": created_at,
        }

    def strategy_survival_analysis_latest(self, limit: int = 20) -> dict[str, Any]:
        transition = self.regime_transition_detection_latest(limit=limit)
        items: list[dict[str, Any]] = []
        sustain_count = 0
        watch_count = 0
        reduce_count = 0
        retire_count = 0

        for item in list(transition.get("items") or []):
            transition_view = dict(item.get("regime_transition_detection") or {})
            transition_detected = bool(transition_view.get("transition_detected"))
            detection_strength = str(transition_view.get("detection_strength") or "stable")
            gating_decision = str(item.get("strategy_gating_decision") or "shadow")
            compatibility_score = float(item.get("compatibility_score", 0.0) or 0.0)
            family_regime_state = str(item.get("family_regime_state") or "balanced")

            survival_posture = "watch"
            survival_reason = "family_requires_continued_monitoring"

            if gating_decision == "retire":
                survival_posture = "retire"
                survival_reason = "family_has_failed_survival_threshold"
                retire_count += 1
            elif gating_decision == "gate" or (
                transition_detected and detection_strength == "confirmed"
            ):
                survival_posture = "reduce"
                survival_reason = "family_should_be_reduced_under_confirmed_regime_shift"
                reduce_count += 1
            elif gating_decision == "allow" and compatibility_score >= 0.8 and family_regime_state == "risk_on":
                survival_posture = "sustain"
                survival_reason = "family_survives_current_regime_cleanly"
                sustain_count += 1
            else:
                watch_count += 1

            items.append(
                {
                    **item,
                    "strategy_survival_analysis": {
                        "survival_posture": survival_posture,
                        "survival_reason": survival_reason,
                        "survival_reason_codes": [
                            f"gating_decision:{gating_decision}",
                            f"transition_detected:{transition_detected}",
                            f"detection_strength:{detection_strength}",
                            f"compatibility_score:{round(compatibility_score, 6)}",
                            f"family_regime_state:{family_regime_state}",
                        ],
                    },
                }
            )

        system_action = "maintain_strategy_survival_watch"
        if retire_count > 0:
            system_action = "retire_non_surviving_strategies"
        elif reduce_count > 0:
            system_action = "reduce_fragile_strategies_under_transition"
        elif sustain_count > 0 and watch_count == 0:
            system_action = "sustain_regime_aligned_strategies"

        return {
            "status": "ok",
            "run_id": transition.get("run_id"),
            "cycle_id": transition.get("cycle_id"),
            "mode": transition.get("mode"),
            "consumed_run_id": transition.get("consumed_run_id"),
            "consumed_cycle_id": transition.get("consumed_cycle_id"),
            "items": items,
            "current_regime": transition.get("current_regime"),
            "regime_confidence": transition.get("regime_confidence"),
            "supporting_signals": transition.get("supporting_signals") or {},
            "system_regime_action": transition.get("system_regime_action"),
            "source_packets": transition.get("source_packets") or {},
            "regime_state_summary": transition.get("regime_state_summary") or {},
            "strategy_regime_compatibility_summary": transition.get("strategy_regime_compatibility_summary") or {},
            "strategy_gating_decision_summary": transition.get("strategy_gating_decision_summary") or {},
            "regime_transition_detection_summary": transition.get("regime_transition_detection_summary") or {},
            "strategy_survival_analysis_summary": {
                "family_count": len(items),
                "sustain_families": sustain_count,
                "watch_families": watch_count,
                "reduce_families": reduce_count,
                "retire_families": retire_count,
                "system_strategy_survival_action": system_action,
            },
            "as_of": transition.get("as_of"),
        }
