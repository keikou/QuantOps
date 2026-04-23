from __future__ import annotations

from typing import Any

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
