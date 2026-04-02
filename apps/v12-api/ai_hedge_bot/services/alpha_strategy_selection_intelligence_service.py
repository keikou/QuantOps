from __future__ import annotations

from typing import Any

from ai_hedge_bot.autonomous_alpha.service import AutonomousAlphaService
from ai_hedge_bot.services.governance_runtime_control_service import GovernanceRuntimeControlService
from ai_hedge_bot.services.portfolio_intelligence_service import PortfolioIntelligenceService


class AlphaStrategySelectionIntelligenceService:
    PRIORITIZE_THRESHOLD = 0.7
    HOLD_THRESHOLD = 0.52
    DEPRIORITIZE_THRESHOLD = 0.36
    PROMOTE_THRESHOLD = 0.72
    SHADOW_THRESHOLD = 0.5
    MAX_PROMOTION_CANDIDATES_PER_FAMILY = 1
    MAX_SHADOW_REVIEW_PER_FAMILY = 1

    def __init__(self) -> None:
        self.alpha = AutonomousAlphaService()
        self.governance = GovernanceRuntimeControlService()
        self.portfolio = PortfolioIntelligenceService()

    @staticmethod
    def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
        return max(lower, min(upper, value))

    def _latest_alpha_meta(self, alpha_id: str) -> dict[str, Any]:
        return self.alpha.store.fetchone_dict(
            "SELECT * FROM alpha_registry WHERE alpha_id=? ORDER BY created_at DESC LIMIT 1",
            [alpha_id],
        ) or {}

    def _positions_by_symbol(self) -> dict[str, dict[str, Any]]:
        overview = self.portfolio.repo.latest_portfolio_overview()
        return {
            str(row.get("symbol") or ""): row for row in list(overview.get("positions") or [])
        }

    def _family_tradeoff_adjustments(self, positions_by_symbol: dict[str, dict[str, Any]]) -> dict[str, float]:
        payload = self.portfolio.allocation_tradeoff_resolution_latest()
        scores: dict[str, list[float]] = {}
        for item in list(payload.get("items") or []):
            symbol = str(item.get("symbol") or "")
            family = str((positions_by_symbol.get(symbol) or {}).get("alpha_family") or "")
            if not family:
                continue
            action = str(item.get("resolved_allocation_action") or "hold")
            tradeoff_score = float(item.get("tradeoff_score", 0.0) or 0.0)
            score = 0.0
            if action == "increase":
                score += 0.1
            elif action == "hold":
                score += 0.03
            elif action == "trim":
                score -= 0.08
            elif action == "zero":
                score -= 0.15
            elif action == "defer":
                score -= 0.05
            score += max(-0.08, min(0.08, tradeoff_score - 0.5))
            scores.setdefault(family, []).append(score)
        return {
            family: round(self._clamp(sum(values) / len(values), -0.2, 0.15), 6)
            for family, values in scores.items()
            if values
        }

    def _family_effectiveness_adjustments(self, positions_by_symbol: dict[str, dict[str, Any]]) -> dict[str, float]:
        payload = self.portfolio.allocation_outcome_effectiveness_latest()
        scores: dict[str, list[float]] = {}
        effect_map = {"beneficial": 0.12, "neutral": 0.0, "adverse": -0.12}
        for item in list(payload.get("items") or []):
            symbol = str(item.get("symbol") or "")
            family = str((positions_by_symbol.get(symbol) or {}).get("alpha_family") or "")
            if not family:
                continue
            effect = str(item.get("realized_effect") or "neutral")
            scores.setdefault(family, []).append(effect_map.get(effect, 0.0))
        return {
            family: round(self._clamp(sum(values) / len(values), -0.15, 0.15), 6)
            for family, values in scores.items()
            if values
        }

    def _control_penalty(self) -> tuple[float, dict[str, Any]]:
        arbitration = self.governance.cross_control_policy_arbitration_latest()
        slippage_guard = self.governance.slippage_guard_latest()
        route_count = max(int((arbitration.get("decision_summary") or {}).get("route_count", 0) or 0), 1)
        conflicted_routes = int((arbitration.get("decision_summary") or {}).get("conflicted_routes", 0) or 0)
        blocking_routes = int((arbitration.get("decision_summary") or {}).get("blocking_routes", 0) or 0)
        global_decision = str(slippage_guard.get("decision") or "continue")

        penalty = 0.0
        if global_decision == "halt":
            penalty = 1.0
        elif global_decision == "pause":
            penalty = 0.65
        penalty += (conflicted_routes / route_count) * 0.18
        penalty += (blocking_routes / route_count) * 0.3
        return self._clamp(penalty), {
            "run_id": arbitration.get("run_id") or slippage_guard.get("run_id"),
            "cycle_id": arbitration.get("cycle_id") or slippage_guard.get("cycle_id"),
            "mode": arbitration.get("mode") or slippage_guard.get("mode"),
            "global_guard_decision": global_decision,
            "conflicted_routes": conflicted_routes,
            "blocking_routes": blocking_routes,
            "route_count": route_count,
            "as_of": arbitration.get("as_of") or slippage_guard.get("as_of"),
        }

    def selection_latest(self, limit: int = 20) -> dict[str, Any]:
        positions_by_symbol = self._positions_by_symbol()
        family_tradeoff_adjustments = self._family_tradeoff_adjustments(positions_by_symbol)
        family_effectiveness_adjustments = self._family_effectiveness_adjustments(positions_by_symbol)
        control_penalty, control_context = self._control_penalty()
        ranking_rows = list(self.alpha.ranking(limit=limit))

        items: list[dict[str, Any]] = []
        for ranking in ranking_rows:
            alpha_id = str(ranking.get("alpha_id") or "")
            meta = self._latest_alpha_meta(alpha_id)
            alpha_family = str(meta.get("alpha_family") or "unknown")
            execution_sensitivity = float(meta.get("execution_sensitivity", 0.0) or 0.0)
            base_rank_score = float(ranking.get("rank_score", 0.0) or 0.0)
            tradeoff_adjustment = float(family_tradeoff_adjustments.get(alpha_family, 0.0) or 0.0)
            effectiveness_adjustment = float(family_effectiveness_adjustments.get(alpha_family, 0.0) or 0.0)
            execution_penalty = self._clamp(execution_sensitivity)

            selection_score = round(
                self._clamp(
                    base_rank_score
                    - (0.22 * execution_penalty)
                    - (0.18 * control_penalty)
                    + tradeoff_adjustment
                    + effectiveness_adjustment,
                    0.0,
                    1.5,
                ),
                6,
            )

            reason_codes: list[str] = []
            if base_rank_score >= 0.75:
                reason_codes.append("high_base_rank")
            if execution_penalty >= 0.3:
                reason_codes.append("execution_sensitive")
            if tradeoff_adjustment > 0.02:
                reason_codes.append("positive_portfolio_tradeoff_feedback")
            elif tradeoff_adjustment < -0.02:
                reason_codes.append("negative_portfolio_tradeoff_feedback")
            if effectiveness_adjustment > 0.02:
                reason_codes.append("beneficial_realized_allocation_effect")
            elif effectiveness_adjustment < -0.02:
                reason_codes.append("adverse_realized_allocation_effect")
            if control_context.get("global_guard_decision") == "pause":
                reason_codes.append("global_guard_pause")
            elif control_context.get("global_guard_decision") == "halt":
                reason_codes.append("global_guard_halt")
            if int(control_context.get("blocking_routes", 0) or 0) > 0:
                reason_codes.append("runtime_control_blocking_present")
            if not reason_codes:
                reason_codes.append("baseline_selection_score")

            action = "exclude" if control_context.get("global_guard_decision") == "halt" else "hold"
            if action != "exclude":
                if selection_score >= self.PRIORITIZE_THRESHOLD and control_penalty < 0.85:
                    action = "prioritize"
                elif selection_score >= self.HOLD_THRESHOLD:
                    action = "hold"
                elif selection_score >= self.DEPRIORITIZE_THRESHOLD:
                    action = "deprioritize"
                else:
                    action = "exclude"

            items.append(
                {
                    "alpha_id": alpha_id,
                    "alpha_family": alpha_family,
                    "factor_type": meta.get("factor_type"),
                    "state": meta.get("state"),
                    "base_rank_score": base_rank_score,
                    "expected_return": float(ranking.get("expected_return", 0.0) or 0.0),
                    "risk_adjusted_score": float(ranking.get("risk_adjusted_score", 0.0) or 0.0),
                    "execution_cost_adjusted_score": float(ranking.get("execution_cost_adjusted_score", 0.0) or 0.0),
                    "diversification_value": float(ranking.get("diversification_value", 0.0) or 0.0),
                    "recommended_action": ranking.get("recommended_action"),
                    "execution_sensitivity": execution_sensitivity,
                    "execution_penalty": round(execution_penalty, 6),
                    "control_penalty": round(control_penalty, 6),
                    "portfolio_tradeoff_adjustment": round(tradeoff_adjustment, 6),
                    "portfolio_effectiveness_adjustment": round(effectiveness_adjustment, 6),
                    "selection_score": selection_score,
                    "selection_action": action,
                    "reason_codes": reason_codes,
                }
            )

        items.sort(key=lambda item: (-float(item.get("selection_score", 0.0) or 0.0), str(item.get("alpha_id") or "")))
        return {
            "status": "ok",
            "run_id": control_context.get("run_id"),
            "cycle_id": control_context.get("cycle_id"),
            "mode": control_context.get("mode"),
            "items": items,
            "decision_summary": {
                "alpha_count": len(items),
                "prioritized_alphas": sum(1 for item in items if item.get("selection_action") == "prioritize"),
                "held_alphas": sum(1 for item in items if item.get("selection_action") == "hold"),
                "deprioritized_alphas": sum(1 for item in items if item.get("selection_action") == "deprioritize"),
                "excluded_alphas": sum(1 for item in items if item.get("selection_action") == "exclude"),
            },
            "control_context": control_context,
            "as_of": control_context.get("as_of"),
        }

    def strategy_action_latest(self, limit: int = 20) -> dict[str, Any]:
        selection = self.selection_latest(limit=limit)
        control_context = dict(selection.get("control_context") or {})
        global_guard = str(control_context.get("global_guard_decision") or "continue")
        items: list[dict[str, Any]] = []

        for item in list(selection.get("items") or []):
            selection_action = str(item.get("selection_action") or "hold")
            alpha_state = str(item.get("state") or "candidate")
            selection_score = float(item.get("selection_score", 0.0) or 0.0)
            control_penalty = float(item.get("control_penalty", 0.0) or 0.0)

            resolved_strategy_action = "research"
            rationale = "selection_below_threshold"

            if global_guard == "halt":
                resolved_strategy_action = "defer"
                rationale = "global_guard_halt"
            elif selection_action == "prioritize" and selection_score >= self.PROMOTE_THRESHOLD and control_penalty < 0.55:
                resolved_strategy_action = "promote"
                rationale = "high_selection_score_under_control_limits"
            elif selection_action in {"prioritize", "hold"} and selection_score >= self.SHADOW_THRESHOLD:
                resolved_strategy_action = "shadow"
                rationale = "selection_viable_but_not_promotion_ready"
            elif selection_action == "exclude":
                resolved_strategy_action = "defer"
                rationale = "selection_excluded_by_current_constraints"
            else:
                resolved_strategy_action = "research"
                rationale = "selection_deprioritized_or_weak"

            if alpha_state == "promoted" and resolved_strategy_action == "promote":
                resolved_strategy_action = "shadow"
                rationale = "already_promoted_hold_in_shadow_review"

            review_priority = "high"
            if resolved_strategy_action == "promote":
                review_priority = "immediate"
            elif resolved_strategy_action == "shadow":
                review_priority = "high"
            elif resolved_strategy_action == "research":
                review_priority = "medium"
            else:
                review_priority = "deferred"

            items.append(
                {
                    **item,
                    "resolved_strategy_action": resolved_strategy_action,
                    "strategy_action_rationale": rationale,
                    "review_priority": review_priority,
                }
            )

        return {
            "status": "ok",
            "run_id": selection.get("run_id"),
            "cycle_id": selection.get("cycle_id"),
            "mode": selection.get("mode"),
            "items": items,
            "decision_summary": {
                "alpha_count": len(items),
                "promote_actions": sum(1 for item in items if item.get("resolved_strategy_action") == "promote"),
                "shadow_actions": sum(1 for item in items if item.get("resolved_strategy_action") == "shadow"),
                "research_actions": sum(1 for item in items if item.get("resolved_strategy_action") == "research"),
                "defer_actions": sum(1 for item in items if item.get("resolved_strategy_action") == "defer"),
            },
            "control_context": control_context,
            "as_of": selection.get("as_of"),
        }

    def selection_queue_latest(self, limit: int = 20) -> dict[str, Any]:
        strategy_actions = self.strategy_action_latest(limit=limit)
        items: list[dict[str, Any]] = []
        for item in list(strategy_actions.get("items") or []):
            resolved_strategy_action = str(item.get("resolved_strategy_action") or "research")
            selection_score = float(item.get("selection_score", 0.0) or 0.0)
            queue_name = "research_return"
            queue_priority = "normal"

            if resolved_strategy_action == "promote":
                queue_name = "promotion_candidate"
                queue_priority = "highest"
            elif resolved_strategy_action == "shadow":
                queue_name = "shadow_review"
                queue_priority = "high"
            elif resolved_strategy_action == "defer":
                queue_name = "deferred_watchlist"
                queue_priority = "low"
            elif selection_score < self.DEPRIORITIZE_THRESHOLD:
                queue_name = "research_return"
                queue_priority = "low"

            items.append(
                {
                    **item,
                    "queue_name": queue_name,
                    "queue_priority": queue_priority,
                    "queue_reason": f"{resolved_strategy_action}_mapped_to_{queue_name}",
                }
            )

        return {
            "status": "ok",
            "run_id": strategy_actions.get("run_id"),
            "cycle_id": strategy_actions.get("cycle_id"),
            "mode": strategy_actions.get("mode"),
            "items": items,
            "decision_summary": {
                "alpha_count": len(items),
                "promotion_candidate_count": sum(1 for item in items if item.get("queue_name") == "promotion_candidate"),
                "shadow_review_count": sum(1 for item in items if item.get("queue_name") == "shadow_review"),
                "research_return_count": sum(1 for item in items if item.get("queue_name") == "research_return"),
                "deferred_watchlist_count": sum(1 for item in items if item.get("queue_name") == "deferred_watchlist"),
            },
            "control_context": strategy_actions.get("control_context"),
            "as_of": strategy_actions.get("as_of"),
        }

    def family_budget_arbitration_latest(self, limit: int = 20) -> dict[str, Any]:
        queues = self.selection_queue_latest(limit=limit)
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
        passthrough_items: list[dict[str, Any]] = []
        for item in list(queues.get("items") or []):
            queue_name = str(item.get("queue_name") or "")
            family = str(item.get("alpha_family") or "unknown")
            if queue_name in {"promotion_candidate", "shadow_review"}:
                grouped.setdefault((family, queue_name), []).append(item)
            else:
                passthrough_items.append(
                    {
                        **item,
                        "arbitrated_queue_name": queue_name,
                        "family_budget_state": "not_budget_limited",
                        "family_rank": 1,
                        "winning_in_family": True,
                    }
                )

        arbitrated_items: list[dict[str, Any]] = []
        for (family, queue_name), items in grouped.items():
            items.sort(
                key=lambda item: (
                    -float(item.get("selection_score", 0.0) or 0.0),
                    -float(item.get("diversification_value", 0.0) or 0.0),
                    str(item.get("alpha_id") or ""),
                )
            )
            budget = (
                self.MAX_PROMOTION_CANDIDATES_PER_FAMILY
                if queue_name == "promotion_candidate"
                else self.MAX_SHADOW_REVIEW_PER_FAMILY
            )
            fallback_queue = "shadow_review" if queue_name == "promotion_candidate" else "research_return"
            for index, item in enumerate(items, start=1):
                winning = index <= budget
                arbitrated_items.append(
                    {
                        **item,
                        "arbitrated_queue_name": queue_name if winning else fallback_queue,
                        "family_budget_state": "within_budget" if winning else "deferred_by_family_budget",
                        "family_rank": index,
                        "winning_in_family": winning,
                    }
                )

        all_items = passthrough_items + arbitrated_items
        all_items.sort(
            key=lambda item: (
                str(item.get("alpha_family") or ""),
                str(item.get("arbitrated_queue_name") or ""),
                int(item.get("family_rank", 9999) or 9999),
                -float(item.get("selection_score", 0.0) or 0.0),
                str(item.get("alpha_id") or ""),
            )
        )

        return {
            "status": "ok",
            "run_id": queues.get("run_id"),
            "cycle_id": queues.get("cycle_id"),
            "mode": queues.get("mode"),
            "items": all_items,
            "decision_summary": {
                "alpha_count": len(all_items),
                "promotion_candidate_count": sum(1 for item in all_items if item.get("arbitrated_queue_name") == "promotion_candidate"),
                "shadow_review_count": sum(1 for item in all_items if item.get("arbitrated_queue_name") == "shadow_review"),
                "research_return_count": sum(1 for item in all_items if item.get("arbitrated_queue_name") == "research_return"),
                "deferred_watchlist_count": sum(1 for item in all_items if item.get("arbitrated_queue_name") == "deferred_watchlist"),
                "family_budget_deferrals": sum(1 for item in all_items if item.get("family_budget_state") == "deferred_by_family_budget"),
            },
            "family_budget_policy": {
                "max_promotion_candidates_per_family": self.MAX_PROMOTION_CANDIDATES_PER_FAMILY,
                "max_shadow_review_per_family": self.MAX_SHADOW_REVIEW_PER_FAMILY,
            },
            "control_context": queues.get("control_context"),
            "as_of": queues.get("as_of"),
        }

    def effective_selection_slate_latest(self, limit: int = 20) -> dict[str, Any]:
        arbitration = self.family_budget_arbitration_latest(limit=limit)
        items: list[dict[str, Any]] = []
        for item in list(arbitration.get("items") or []):
            arbitrated_queue_name = str(item.get("arbitrated_queue_name") or "")
            effective_status = "rejected"
            if arbitrated_queue_name == "promotion_candidate":
                effective_status = "selected_for_promotion_review"
            elif arbitrated_queue_name == "shadow_review":
                effective_status = "selected_for_shadow_review"
            elif arbitrated_queue_name == "research_return":
                effective_status = "returned_to_research"
            elif arbitrated_queue_name == "deferred_watchlist":
                effective_status = "deferred"

            items.append(
                {
                    **item,
                    "effective_status": effective_status,
                }
            )

        return {
            "status": "ok",
            "run_id": arbitration.get("run_id"),
            "cycle_id": arbitration.get("cycle_id"),
            "mode": arbitration.get("mode"),
            "items": items,
            "decision_summary": {
                "alpha_count": len(items),
                "selected_for_promotion_review": sum(1 for item in items if item.get("effective_status") == "selected_for_promotion_review"),
                "selected_for_shadow_review": sum(1 for item in items if item.get("effective_status") == "selected_for_shadow_review"),
                "returned_to_research": sum(1 for item in items if item.get("effective_status") == "returned_to_research"),
                "deferred": sum(1 for item in items if item.get("effective_status") == "deferred"),
            },
            "family_budget_policy": arbitration.get("family_budget_policy"),
            "control_context": arbitration.get("control_context"),
            "as_of": arbitration.get("as_of"),
        }
