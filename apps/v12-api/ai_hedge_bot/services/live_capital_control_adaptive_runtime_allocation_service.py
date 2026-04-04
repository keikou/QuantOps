from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from typing import Any

from ai_hedge_bot.services.deployment_rollout_intelligence_service import (
    DeploymentRolloutIntelligenceService,
)
from ai_hedge_bot.services.governance_runtime_control_service import (
    GovernanceRuntimeControlService,
)
from ai_hedge_bot.services.portfolio_intelligence_service import PortfolioIntelligenceService


class LiveCapitalControlAdaptiveRuntimeAllocationService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.deployment_rollout = DeploymentRolloutIntelligenceService()
        self.governance = GovernanceRuntimeControlService()
        self.portfolio = PortfolioIntelligenceService()

    @staticmethod
    def _mode_from_action(action: str) -> str:
        normalized = str(action or "keep").lower()
        if normalized in {"freeze", "halt", "stop", "block", "zero"}:
            return "frozen"
        if normalized in {"reduce", "degrade", "pause", "throttle", "trim"}:
            return "degraded"
        return "live"

    @staticmethod
    def _scaling_band(capital_cap: float) -> str:
        if capital_cap <= 0.0:
            return "frozen"
        if capital_cap < 0.5:
            return "tight"
        if capital_cap < 1.0:
            return "reduced"
        return "normal"

    def latest(self, limit: int = 20) -> dict[str, Any]:
        rollout = self.deployment_rollout.rollout_outcome_effectiveness_latest(limit=limit)
        governance = self.governance.cross_control_policy_arbitration_latest()
        allocation = self.portfolio.execution_aware_capital_allocation_latest()

        governance_items = list(governance.get("items") or [])
        allocation_items = list(allocation.get("items") or [])
        avg_multiplier = 1.0
        if allocation_items:
            avg_multiplier = sum(
                float(item.get("target_capital_multiplier", 1.0) or 1.0) for item in allocation_items
            ) / len(allocation_items)

        frozen_routes = sum(
            1
            for item in governance_items
            if self._mode_from_action(str(item.get("resolved_runtime_action") or "allow")) == "frozen"
        )
        degraded_routes = sum(
            1
            for item in governance_items
            if self._mode_from_action(str(item.get("resolved_runtime_action") or "allow")) == "degraded"
        )

        items: list[dict[str, Any]] = []
        live_count = 0
        degraded_count = 0
        frozen_count = 0

        for item in list(rollout.get("items") or []):
            realized_effect = str(item.get("realized_effect") or "neutral")
            rollout_stage = str(item.get("recommended_rollout_stage") or "limited")

            effective_live_capital = avg_multiplier
            risk_budget_cap = avg_multiplier
            live_control_action = "keep"

            if realized_effect == "adverse" or frozen_routes > 0:
                effective_live_capital = 0.0
                risk_budget_cap = 0.0
                live_control_action = "freeze"
                frozen_count += 1
            elif realized_effect == "neutral" or degraded_routes > 0:
                effective_live_capital = min(avg_multiplier, 0.5)
                risk_budget_cap = min(avg_multiplier, 0.5)
                live_control_action = "reduce"
                degraded_count += 1
            else:
                if rollout_stage == "full":
                    effective_live_capital = max(avg_multiplier, 1.0)
                    risk_budget_cap = max(avg_multiplier, 1.0)
                    live_control_action = "keep"
                    live_count += 1
                elif rollout_stage == "canary":
                    effective_live_capital = min(max(avg_multiplier, 0.5), 0.75)
                    risk_budget_cap = min(max(avg_multiplier, 0.5), 0.75)
                    live_control_action = "degrade"
                    degraded_count += 1
                else:
                    effective_live_capital = min(avg_multiplier, 0.5)
                    risk_budget_cap = min(avg_multiplier, 0.5)
                    live_control_action = "reduce"
                    degraded_count += 1

            items.append(
                {
                    "alpha_family": item.get("alpha_family"),
                    "run_id": rollout.get("run_id"),
                    "cycle_id": rollout.get("cycle_id"),
                    "consumed_run_id": rollout.get("consumed_run_id"),
                    "consumed_cycle_id": rollout.get("consumed_cycle_id"),
                    "recommended_rollout_stage": rollout_stage,
                    "realized_effect": realized_effect,
                    "effective_live_capital": round(effective_live_capital, 6),
                    "risk_budget_cap": round(risk_budget_cap, 6),
                    "current_mode": self._mode_from_action(live_control_action),
                    "allowed_scaling_band": self._scaling_band(effective_live_capital),
                    "live_control_action": live_control_action,
                    "current_limits": {
                        "frozen_routes": frozen_routes,
                        "degraded_routes": degraded_routes,
                    },
                    "current_health": {
                        "portfolio_capital_multiplier": round(avg_multiplier, 6),
                        "rollout_effectiveness": realized_effect,
                    },
                }
            )

        system_live_capital_action = "keep_live_capital"
        if frozen_count > 0:
            system_live_capital_action = "freeze_stressed_live_capital"
        elif degraded_count > 0:
            system_live_capital_action = "reduce_live_capital_under_current_truth"

        return {
            "status": "ok",
            "run_id": rollout.get("run_id"),
            "cycle_id": rollout.get("cycle_id"),
            "mode": rollout.get("mode"),
            "consumed_run_id": rollout.get("consumed_run_id"),
            "consumed_cycle_id": rollout.get("consumed_cycle_id"),
            "items": items,
            "cross_layer_coherence": rollout.get("cross_layer_coherence") or {},
            "source_packets": {
                "deployment_rollout_intelligence": "DRI-05",
                "governance_runtime_control": "C6",
                "portfolio_intelligence": "PI-05",
            },
            "live_capital_control_summary": {
                "family_count": len(items),
                "live_families": live_count,
                "degraded_families": degraded_count,
                "frozen_families": frozen_count,
                "system_live_capital_action": system_live_capital_action,
            },
            "as_of": rollout.get("as_of"),
        }

    def adjustment_decision_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.latest(limit=limit)
        items: list[dict[str, Any]] = []
        keep_count = 0
        scale_up_count = 0
        scale_down_count = 0
        freeze_count = 0
        revert_count = 0

        for item in list(payload.get("items") or []):
            current_mode = str(item.get("current_mode") or "live")
            rollout_stage = str(item.get("recommended_rollout_stage") or "limited")
            realized_effect = str(item.get("realized_effect") or "neutral")

            decision = "keep"
            reason = "live_truth_supports_current_allocation"

            if current_mode == "frozen":
                if rollout_stage == "shadow":
                    decision = "revert_to_shadow"
                    reason = "live_truth_requires_shadow_reversion"
                    revert_count += 1
                else:
                    decision = "freeze"
                    reason = "live_truth_requires_freeze"
                    freeze_count += 1
            elif current_mode == "degraded":
                decision = "scale_down"
                reason = "live_truth_requires_capital_reduction"
                scale_down_count += 1
            elif realized_effect == "beneficial" and rollout_stage == "full":
                decision = "scale_up"
                reason = "live_truth_supports_controlled_scale_up"
                scale_up_count += 1
            else:
                keep_count += 1

            items.append(
                {
                    **item,
                    "capital_adjustment_decision": decision,
                    "decision_reason": reason,
                }
            )

        system_adjustment_action = "keep_current_live_allocation"
        if revert_count > 0:
            system_adjustment_action = "revert_stressed_live_allocations_to_shadow"
        elif freeze_count > 0:
            system_adjustment_action = "freeze_stressed_live_allocations"
        elif scale_down_count > 0:
            system_adjustment_action = "scale_down_live_allocations"
        elif scale_up_count > 0:
            system_adjustment_action = "scale_up_live_allocations_selectively"

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
            "live_capital_control_summary": payload.get("live_capital_control_summary") or {},
            "live_capital_adjustment_summary": {
                "family_count": len(items),
                "keep_families": keep_count,
                "scale_up_families": scale_up_count,
                "scale_down_families": scale_down_count,
                "freeze_families": freeze_count,
                "revert_to_shadow_families": revert_count,
                "system_adjustment_action": system_adjustment_action,
            },
            "as_of": payload.get("as_of"),
        }

    def control_state_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.adjustment_decision_latest(limit=limit)
        created_at = utc_now_iso()
        items: list[dict[str, Any]] = []
        live_count = 0
        degraded_count = 0
        frozen_count = 0
        reduced_count = 0

        for item in list(payload.get("items") or []):
            family = str(item.get("alpha_family") or "unknown")
            previous_state = self.store.fetchone_dict(
                """
                SELECT *
                FROM audit_logs
                WHERE category='live_capital_control_state'
                  AND actor=?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                [family],
            ) or {}

            control_state = str(item.get("current_mode") or "live")
            if control_state == "live":
                live_count += 1
            elif control_state == "frozen":
                frozen_count += 1
            elif str(item.get("capital_adjustment_decision") or "") == "scale_down":
                control_state = "reduced"
                reduced_count += 1
            else:
                degraded_count += 1

            control_state_id = new_cycle_id()
            self.store.append(
                "audit_logs",
                {
                    "audit_id": control_state_id,
                    "created_at": created_at,
                    "category": "live_capital_control_state",
                    "event_type": "persist_live_capital_control_state",
                    "run_id": payload.get("run_id"),
                    "payload_json": self.store.to_json(
                        {
                            "alpha_family": family,
                            "run_id": payload.get("run_id"),
                            "cycle_id": payload.get("cycle_id"),
                            "mode": payload.get("mode"),
                            "control_state": control_state,
                            "capital_adjustment_decision": item.get("capital_adjustment_decision"),
                            "effective_live_capital": item.get("effective_live_capital"),
                            "risk_budget_cap": item.get("risk_budget_cap"),
                            "control_source_packet": "LCC-02",
                        }
                    ),
                    "actor": family,
                },
            )

            items.append(
                {
                    **item,
                    "control_state": control_state,
                    "control_state_id": control_state_id,
                    "previous_control_state_id": previous_state.get("audit_id"),
                    "decision_age_seconds": 0,
                    "last_control_tick": created_at,
                    "stale_flag": False,
                    "control_source_packet": "LCC-02",
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
            "live_capital_control_summary": payload.get("live_capital_control_summary") or {},
            "live_capital_adjustment_summary": payload.get("live_capital_adjustment_summary") or {},
            "live_capital_control_state_summary": {
                "family_count": len(items),
                "live_families": live_count,
                "degraded_families": degraded_count,
                "reduced_families": reduced_count,
                "frozen_families": frozen_count,
                "system_control_state_action": "persist_live_capital_control_state",
            },
            "as_of": created_at,
        }

    def control_consumption_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.control_state_latest(limit=limit)
        consumed_run_id = f"{payload.get('run_id') or 'unknown'}:live-next"
        consumed_cycle_id = f"{payload.get('cycle_id') or 'unknown'}:live-next"
        items: list[dict[str, Any]] = []
        live_count = 0
        reduced_count = 0
        frozen_count = 0

        for item in list(payload.get("items") or []):
            control_state = str(item.get("control_state") or "live")
            effective_live_capital = float(item.get("effective_live_capital", 0.0) or 0.0)
            risk_budget_cap = float(item.get("risk_budget_cap", 0.0) or 0.0)

            if control_state == "frozen":
                used_capital = 0.0
                used_risk = 0.0
                frozen_count += 1
            elif control_state in {"reduced", "degraded"}:
                used_capital = round(effective_live_capital * 0.8, 6)
                used_risk = round(risk_budget_cap * 0.8, 6)
                reduced_count += 1
            else:
                used_capital = round(effective_live_capital * 0.9, 6)
                used_risk = round(risk_budget_cap * 0.9, 6)
                live_count += 1

            headroom = round(max(effective_live_capital - used_capital, 0.0), 6)
            utilization_ratio = 0.0 if effective_live_capital <= 0.0 else round(used_capital / effective_live_capital, 6)

            items.append(
                {
                    **item,
                    "consumed_run_id": consumed_run_id,
                    "consumed_cycle_id": consumed_cycle_id,
                    "live_capital_control_consumption": {
                        "used_capital": used_capital,
                        "used_risk": used_risk,
                        "headroom": headroom,
                        "utilization_ratio": utilization_ratio,
                    },
                }
            )

        system_consumption_action = "consume_frozen_live_budget"
        if live_count > 0:
            system_consumption_action = "consume_live_budget_with_headroom"
        elif reduced_count > 0:
            system_consumption_action = "consume_reduced_live_budget"

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
            "live_capital_control_summary": payload.get("live_capital_control_summary") or {},
            "live_capital_adjustment_summary": payload.get("live_capital_adjustment_summary") or {},
            "live_capital_control_state_summary": payload.get("live_capital_control_state_summary") or {},
            "live_capital_control_consumption_summary": {
                "family_count": len(items),
                "live_consumptions": live_count,
                "reduced_consumptions": reduced_count,
                "frozen_consumptions": frozen_count,
                "system_consumption_action": system_consumption_action,
            },
            "as_of": payload.get("as_of"),
        }

    def control_effectiveness_latest(self, limit: int = 20) -> dict[str, Any]:
        payload = self.control_consumption_latest(limit=limit)
        items: list[dict[str, Any]] = []
        beneficial_count = 0
        neutral_count = 0
        adverse_count = 0

        for item in list(payload.get("items") or []):
            control_state = str(item.get("control_state") or "live")
            utilization_ratio = float(
                dict(item.get("live_capital_control_consumption") or {}).get("utilization_ratio", 0.0) or 0.0
            )
            headroom = float(dict(item.get("live_capital_control_consumption") or {}).get("headroom", 0.0) or 0.0)

            realized_effect = "neutral"
            if control_state == "live" and utilization_ratio <= 0.9:
                realized_effect = "beneficial"
                beneficial_count += 1
            elif control_state in {"frozen", "reduced"} and headroom >= 0.0:
                realized_effect = "neutral"
                neutral_count += 1
            else:
                realized_effect = "adverse"
                adverse_count += 1

            items.append(
                {
                    **item,
                    "intended_objective": "maintain_adaptive_live_capital_control",
                    "realized_effect": realized_effect,
                    "effectiveness_reason_codes": [
                        f"control_state:{control_state}",
                        f"utilization_ratio:{utilization_ratio}",
                        f"realized_effect:{realized_effect}",
                    ],
                }
            )

        system_effectiveness_action = "observe_live_capital_control_effectiveness"
        if adverse_count > 0:
            system_effectiveness_action = "rework_live_capital_control_policy"
        elif beneficial_count > 0:
            system_effectiveness_action = "reinforce_live_capital_control_policy"

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
            "live_capital_control_summary": payload.get("live_capital_control_summary") or {},
            "live_capital_adjustment_summary": payload.get("live_capital_adjustment_summary") or {},
            "live_capital_control_state_summary": payload.get("live_capital_control_state_summary") or {},
            "live_capital_control_consumption_summary": payload.get("live_capital_control_consumption_summary") or {},
            "live_capital_control_effectiveness_summary": {
                "family_count": len(items),
                "beneficial_families": beneficial_count,
                "neutral_families": neutral_count,
                "adverse_families": adverse_count,
                "system_effectiveness_action": system_effectiveness_action,
            },
            "as_of": payload.get("as_of"),
        }
