from __future__ import annotations

from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.services.live_capital_control_adaptive_runtime_allocation_service import (
    LiveCapitalControlAdaptiveRuntimeAllocationService,
)
from ai_hedge_bot.services.portfolio_intelligence_service import PortfolioIntelligenceService


class MetaPortfolioIntelligenceCrossStrategyCapitalAllocationService:
    ACTION_SHIFT_THRESHOLD = 0.05
    FLOW_MATERIALITY_THRESHOLD = 0.1

    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.live_capital_control = LiveCapitalControlAdaptiveRuntimeAllocationService()
        self.portfolio = PortfolioIntelligenceService()

    @staticmethod
    def _effect_score(realized_effect: str) -> float:
        normalized = str(realized_effect or "neutral").lower()
        if normalized == "beneficial":
            return 1.0
        if normalized == "adverse":
            return 0.2
        return 0.6

    @staticmethod
    def _state_multiplier(control_state: str) -> float:
        normalized = str(control_state or "live").lower()
        if normalized == "frozen":
            return 0.0
        if normalized == "reduced":
            return 0.55
        if normalized == "degraded":
            return 0.7
        return 1.0

    def latest(self, limit: int = 20) -> dict[str, Any]:
        live_capital = self.live_capital_control.control_effectiveness_latest(limit=limit)
        portfolio = self.portfolio.execution_aware_capital_allocation_latest()

        portfolio_items = list(portfolio.get("items") or [])
        portfolio_multiplier = 1.0
        if portfolio_items:
            portfolio_multiplier = sum(
                float(item.get("target_capital_multiplier", 1.0) or 1.0) for item in portfolio_items
            ) / len(portfolio_items)

        live_items = list(live_capital.get("items") or [])
        total_effective_capital = sum(
            float(item.get("effective_live_capital", 0.0) or 0.0) for item in live_items
        )
        total_effective_capital = max(total_effective_capital, 1e-9)

        raw_targets: list[float] = []
        prepared_items: list[dict[str, Any]] = []
        for item in live_items:
            control_state = str(item.get("control_state") or item.get("current_mode") or "live")
            realized_effect = str(item.get("realized_effect") or "neutral")
            effective_live_capital = float(item.get("effective_live_capital", 0.0) or 0.0)
            risk_budget_cap = float(item.get("risk_budget_cap", 0.0) or 0.0)
            consumption = dict(item.get("live_capital_control_consumption") or {})
            utilization_ratio = float(consumption.get("utilization_ratio", 0.0) or 0.0)

            effect_score = self._effect_score(realized_effect)
            state_multiplier = self._state_multiplier(control_state)
            marginal_efficiency_score = round(
                max(
                    0.0,
                    ((0.65 * effect_score) + (0.35 * min(max(utilization_ratio, 0.0), 1.25)))
                    * state_multiplier
                    * max(portfolio_multiplier, 0.0),
                ),
                6,
            )
            raw_target = max(marginal_efficiency_score * max(risk_budget_cap, 0.0), 0.0)
            raw_targets.append(raw_target)
            prepared_items.append(
                {
                    **item,
                    "control_state": control_state,
                    "realized_effect": realized_effect,
                    "effective_live_capital": round(effective_live_capital, 6),
                    "risk_budget_cap": round(risk_budget_cap, 6),
                    "current_allocation_share": round(effective_live_capital / total_effective_capital, 6),
                    "marginal_efficiency_score": marginal_efficiency_score,
                    "portfolio_capital_multiplier": round(portfolio_multiplier, 6),
                    "_raw_target": raw_target,
                }
            )

        total_raw_target = max(sum(raw_targets), 1e-9)
        items: list[dict[str, Any]] = []
        shift_in_count = 0
        shift_out_count = 0
        hold_count = 0
        frozen_count = 0

        for item in prepared_items:
            current_share = float(item.get("current_allocation_share", 0.0) or 0.0)
            target_share = round(float(item.get("_raw_target", 0.0) or 0.0) / total_raw_target, 6)
            share_delta = round(target_share - current_share, 6)
            control_state = str(item.get("control_state") or "live")

            allocation_action = "hold"
            reason = "capital_competition_balanced"
            if control_state == "frozen" or target_share <= 0.0:
                allocation_action = "freeze"
                reason = "family_not_eligible_for_capital"
                frozen_count += 1
            elif share_delta >= self.ACTION_SHIFT_THRESHOLD:
                allocation_action = "shift_in"
                reason = "family_has_superior_marginal_efficiency"
                shift_in_count += 1
            elif share_delta <= -self.ACTION_SHIFT_THRESHOLD:
                allocation_action = "shift_out"
                reason = "family_has_inferior_marginal_efficiency"
                shift_out_count += 1
            else:
                hold_count += 1

            items.append(
                {
                    key: value for key, value in item.items() if not key.startswith("_")
                }
                | {
                    "target_allocation_share": target_share,
                    "allocation_share_delta": share_delta,
                    "allocation_action": allocation_action,
                    "allocation_reason": reason,
                }
            )

        system_action = "hold_meta_portfolio_allocation"
        if frozen_count > 0:
            system_action = "remove_ineligible_families_from_meta_portfolio"
        elif shift_in_count > 0 and shift_out_count > 0:
            system_action = "reallocate_capital_across_live_families"
        elif shift_in_count > 0:
            system_action = "concentrate_meta_portfolio_selectively"
        elif shift_out_count > 0:
            system_action = "deconcentrate_weaker_families"

        return {
            "status": "ok",
            "run_id": live_capital.get("run_id"),
            "cycle_id": live_capital.get("cycle_id"),
            "mode": live_capital.get("mode"),
            "consumed_run_id": live_capital.get("consumed_run_id"),
            "consumed_cycle_id": live_capital.get("consumed_cycle_id"),
            "items": items,
            "cross_layer_coherence": live_capital.get("cross_layer_coherence") or {},
            "source_packets": {
                "live_capital_control": "LCC-05",
                "portfolio_intelligence": "PI-05",
            },
            "meta_portfolio_allocation_summary": {
                "family_count": len(items),
                "shift_in_families": shift_in_count,
                "shift_out_families": shift_out_count,
                "hold_families": hold_count,
                "frozen_families": frozen_count,
                "system_meta_portfolio_action": system_action,
            },
            "as_of": live_capital.get("as_of"),
        }

    def decision_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.latest(limit=limit)
        items: list[dict[str, Any]] = []
        shift_count = 0
        hold_count = 0
        freeze_count = 0
        rebalance_count = 0

        for item in list(payload.get("items") or []):
            action = str(item.get("allocation_action") or "hold")
            delta = float(item.get("allocation_share_delta", 0.0) or 0.0)
            current_share = float(item.get("current_allocation_share", 0.0) or 0.0)
            target_share = float(item.get("target_allocation_share", 0.0) or 0.0)

            decision = "hold"
            reason = "meta_portfolio_balance_preserved"
            if action == "freeze":
                decision = "freeze"
                reason = "family_removed_from_capital_competition"
                freeze_count += 1
            elif abs(delta) >= self.FLOW_MATERIALITY_THRESHOLD:
                decision = "rebalance"
                reason = "material_cross_strategy_reallocation_required"
                rebalance_count += 1
            elif action in {"shift_in", "shift_out"}:
                decision = "shift"
                reason = "family_share_should_move_incrementally"
                shift_count += 1
            else:
                hold_count += 1

            items.append(
                {
                    **item,
                    "meta_portfolio_decision": decision,
                    "decision_reason": reason,
                    "capital_flow_hint": {
                        "from_share": round(current_share, 6),
                        "to_share": round(target_share, 6),
                        "material_change": abs(delta) >= self.FLOW_MATERIALITY_THRESHOLD,
                    },
                }
            )

        system_action = "hold_meta_portfolio_decisions"
        if freeze_count > 0:
            system_action = "freeze_ineligible_meta_portfolio_families"
        elif rebalance_count > 0:
            system_action = "rebalance_meta_portfolio_capital"
        elif shift_count > 0:
            system_action = "shift_meta_portfolio_capital_incrementally"

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
            "meta_portfolio_allocation_summary": payload.get("meta_portfolio_allocation_summary") or {},
            "meta_portfolio_decision_summary": {
                "family_count": len(items),
                "shift_families": shift_count,
                "rebalance_families": rebalance_count,
                "hold_families": hold_count,
                "freeze_families": freeze_count,
                "system_meta_portfolio_decision_action": system_action,
            },
            "as_of": payload.get("as_of"),
        }

    def state_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.decision_latest(limit=limit)
        created_at = utc_now_iso()
        items: list[dict[str, Any]] = []
        balanced_count = 0
        concentrated_count = 0
        unstable_count = 0
        frozen_count = 0

        for item in list(payload.get("items") or []):
            family = str(item.get("alpha_family") or "unknown")
            previous_state = self.store.fetchone_dict(
                """
                SELECT *
                FROM audit_logs
                WHERE category='meta_portfolio_state'
                  AND actor=?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                [family],
            ) or {}

            decision = str(item.get("meta_portfolio_decision") or "hold")
            flow_hint = dict(item.get("capital_flow_hint") or {})
            material_change = bool(flow_hint.get("material_change"))

            state = "balanced"
            if decision == "freeze":
                state = "frozen"
                frozen_count += 1
            elif decision == "rebalance":
                state = "unstable"
                unstable_count += 1
            elif decision == "shift":
                state = "concentrated"
                concentrated_count += 1
            else:
                balanced_count += 1

            state_id = new_cycle_id()
            self.store.append(
                "audit_logs",
                {
                    "audit_id": state_id,
                    "created_at": created_at,
                    "category": "meta_portfolio_state",
                    "event_type": "persist_meta_portfolio_state",
                    "run_id": payload.get("run_id"),
                    "payload_json": self.store.to_json(
                        {
                            "alpha_family": family,
                            "run_id": payload.get("run_id"),
                            "cycle_id": payload.get("cycle_id"),
                            "mode": payload.get("mode"),
                            "meta_portfolio_decision": decision,
                            "meta_portfolio_state": state,
                            "target_allocation_share": item.get("target_allocation_share"),
                            "current_allocation_share": item.get("current_allocation_share"),
                            "material_change": material_change,
                            "state_source_packet": "MPI-02",
                        }
                    ),
                    "actor": family,
                },
            )

            items.append(
                {
                    **item,
                    "meta_portfolio_state": state,
                    "meta_portfolio_state_id": state_id,
                    "previous_meta_portfolio_state_id": previous_state.get("audit_id"),
                    "decision_age_seconds": 0,
                    "last_meta_portfolio_tick": created_at,
                    "stale_flag": False,
                    "state_source_packet": "MPI-02",
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
            "meta_portfolio_allocation_summary": payload.get("meta_portfolio_allocation_summary") or {},
            "meta_portfolio_decision_summary": payload.get("meta_portfolio_decision_summary") or {},
            "meta_portfolio_state_summary": {
                "family_count": len(items),
                "balanced_families": balanced_count,
                "concentrated_families": concentrated_count,
                "unstable_families": unstable_count,
                "frozen_families": frozen_count,
                "system_meta_portfolio_state_action": "persist_meta_portfolio_state",
            },
            "as_of": created_at,
        }

    def flow_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.state_latest(limit=limit)
        consumed_run_id = f"{payload.get('run_id') or 'unknown'}:meta-next"
        consumed_cycle_id = f"{payload.get('cycle_id') or 'unknown'}:meta-next"
        items: list[dict[str, Any]] = []
        rebalance_count = 0
        shift_count = 0
        freeze_count = 0
        hold_count = 0

        for item in list(payload.get("items") or []):
            current_share = float(item.get("current_allocation_share", 0.0) or 0.0)
            target_share = float(item.get("target_allocation_share", 0.0) or 0.0)
            moved_share = round(target_share - current_share, 6)
            decision = str(item.get("meta_portfolio_decision") or "hold")

            flow_action = "hold"
            if decision == "freeze":
                flow_action = "remove"
                freeze_count += 1
            elif decision == "rebalance":
                flow_action = "rebalance"
                rebalance_count += 1
            elif decision == "shift":
                flow_action = "shift"
                shift_count += 1
            else:
                hold_count += 1

            items.append(
                {
                    **item,
                    "consumed_run_id": consumed_run_id,
                    "consumed_cycle_id": consumed_cycle_id,
                    "meta_portfolio_flow": {
                        "from_share": round(current_share, 6),
                        "to_share": round(target_share, 6),
                        "moved_share": moved_share,
                        "flow_action": flow_action,
                    },
                }
            )

        system_action = "hold_meta_portfolio_flow"
        if freeze_count > 0:
            system_action = "remove_frozen_meta_portfolio_families"
        elif rebalance_count > 0:
            system_action = "rebalance_meta_portfolio_flow"
        elif shift_count > 0:
            system_action = "shift_meta_portfolio_flow_incrementally"

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
            "meta_portfolio_allocation_summary": payload.get("meta_portfolio_allocation_summary") or {},
            "meta_portfolio_decision_summary": payload.get("meta_portfolio_decision_summary") or {},
            "meta_portfolio_state_summary": payload.get("meta_portfolio_state_summary") or {},
            "meta_portfolio_flow_summary": {
                "family_count": len(items),
                "rebalance_flows": rebalance_count,
                "shift_flows": shift_count,
                "freeze_flows": freeze_count,
                "hold_flows": hold_count,
                "system_meta_portfolio_flow_action": system_action,
            },
            "as_of": payload.get("as_of"),
        }

    def efficiency_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.flow_latest(limit=limit)
        items: list[dict[str, Any]] = []
        beneficial_count = 0
        neutral_count = 0
        adverse_count = 0

        for item in list(payload.get("items") or []):
            flow = dict(item.get("meta_portfolio_flow") or {})
            flow_action = str(flow.get("flow_action") or "hold")
            moved_share = float(flow.get("moved_share", 0.0) or 0.0)
            efficiency_score = float(item.get("marginal_efficiency_score", 0.0) or 0.0)

            realized_effect = "neutral"
            reason_codes: list[str] = []
            if flow_action in {"shift", "rebalance"} and efficiency_score >= 0.7:
                realized_effect = "beneficial"
                reason_codes.append("capital_moved_toward_high_efficiency_family")
                beneficial_count += 1
            elif flow_action == "remove" and efficiency_score <= 0.25:
                realized_effect = "beneficial"
                reason_codes.append("capital_removed_from_low_efficiency_family")
                beneficial_count += 1
            elif flow_action == "hold" and abs(moved_share) < self.ACTION_SHIFT_THRESHOLD:
                realized_effect = "neutral"
                reason_codes.append("capital_distribution_remained_stable")
                neutral_count += 1
            elif flow_action in {"shift", "rebalance"} and efficiency_score < 0.4:
                realized_effect = "adverse"
                reason_codes.append("capital_moved_without_sufficient_efficiency_support")
                adverse_count += 1
            elif flow_action == "remove" and efficiency_score > 0.4:
                realized_effect = "adverse"
                reason_codes.append("productive_family_was_removed")
                adverse_count += 1
            else:
                neutral_count += 1
                reason_codes.append("mixed_meta_portfolio_efficiency_result")

            items.append(
                {
                    **item,
                    "intended_objective": "allocate_capital_to_best_marginal_opportunity",
                    "realized_effect": realized_effect,
                    "efficiency_reason_codes": reason_codes
                    + [
                        f"flow_action:{flow_action}",
                        f"moved_share:{round(moved_share, 6)}",
                        f"marginal_efficiency_score:{round(efficiency_score, 6)}",
                    ],
                }
            )

        system_action = "observe_meta_portfolio_efficiency"
        if adverse_count > 0:
            system_action = "rework_meta_portfolio_competition_policy"
        elif beneficial_count > 0:
            system_action = "reinforce_meta_portfolio_competition_policy"

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
            "meta_portfolio_allocation_summary": payload.get("meta_portfolio_allocation_summary") or {},
            "meta_portfolio_decision_summary": payload.get("meta_portfolio_decision_summary") or {},
            "meta_portfolio_state_summary": payload.get("meta_portfolio_state_summary") or {},
            "meta_portfolio_flow_summary": payload.get("meta_portfolio_flow_summary") or {},
            "meta_portfolio_efficiency_summary": {
                "family_count": len(items),
                "beneficial_families": beneficial_count,
                "neutral_families": neutral_count,
                "adverse_families": adverse_count,
                "system_meta_portfolio_efficiency_action": system_action,
            },
            "as_of": payload.get("as_of"),
        }
