from __future__ import annotations

import json
from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.autonomous_alpha.service import AutonomousAlphaService
from ai_hedge_bot.research_factory.service import ResearchFactoryService
from ai_hedge_bot.services.strategy_evolution_regime_adaptation_intelligence_service import (
    StrategyEvolutionRegimeAdaptationIntelligenceService,
)


class AutonomousAlphaExpansionStrategyGenerationIntelligenceService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.alpha_factory = AutonomousAlphaService()
        self.research_factory = ResearchFactoryService()
        self.strategy_evolution = StrategyEvolutionRegimeAdaptationIntelligenceService()

    @staticmethod
    def _decode_json(value: Any, default: Any) -> Any:
        if value in (None, ""):
            return default
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(str(value))
        except Exception:
            return default

    @staticmethod
    def _latest_by_key(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for row in rows:
            value = str(row.get(key) or "")
            if value and value not in latest:
                latest[value] = row
        return latest

    def _latest_registry_rows(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_registry
            ORDER BY created_at DESC, alpha_id ASC
            LIMIT ?
            """,
            [max(limit, 50)],
        )
        latest = list(self._latest_by_key(rows, "alpha_id").values())
        for row in latest:
            row["feature_dependencies"] = self._decode_json(row.pop("feature_dependencies_json", "[]"), [])
        return latest[:limit]

    def _latest_eval_rows(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_eval_results
            ORDER BY created_at DESC, alpha_id ASC
            LIMIT ?
            """,
            [max(limit, 50)],
        )
        return list(self._latest_by_key(rows, "alpha_id").values())[:limit]

    def _latest_ranking_rows(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_rankings
            ORDER BY created_at DESC, rank_score DESC, alpha_id ASC
            LIMIT ?
            """,
            [max(limit, 50)],
        )
        return list(self._latest_by_key(rows, "alpha_id").values())[:limit]

    def _latest_status_rows(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_status_events
            ORDER BY created_at DESC, alpha_id ASC
            LIMIT ?
            """,
            [max(limit, 50)],
        )
        return list(self._latest_by_key(rows, "alpha_id").values())[:limit]

    def _latest_library_rows(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_library
            ORDER BY created_at DESC, rank_score DESC, alpha_id ASC
            LIMIT ?
            """,
            [max(limit, 50)],
        )
        latest = list(self._latest_by_key(rows, "alpha_id").values())
        for row in latest:
            row["tags"] = self._decode_json(row.pop("tags_json", "[]"), [])
        return latest[:limit]

    def _latest_experiment_rows(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.research_factory.experiments.list_latest(limit=max(limit, 25))
        return rows[:limit]

    def _latest_validation_rows(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.research_factory.validations.list_latest(limit=max(limit, 25))
        return rows[:limit]

    def _regime_context(self, limit: int = 20) -> dict[str, Any]:
        regime = self.strategy_evolution.latest(limit=limit)
        family_state = {
            str(item.get("alpha_family") or ""): str(item.get("family_regime_state") or "balanced")
            for item in list(regime.get("items") or [])
        }
        return {
            "current_regime": str(regime.get("current_regime") or "balanced"),
            "regime_confidence": float(regime.get("regime_confidence", 0.0) or 0.0),
            "family_regime_state": family_state,
            "system_regime_action": str(regime.get("system_regime_action") or "maintain_current_strategy_posture"),
        }

    @staticmethod
    def _discovery_priority(
        *,
        state: str,
        validation_decision: str,
        family_regime_state: str,
    ) -> tuple[str, float]:
        if validation_decision == "pass" and family_regime_state in {"risk_on", "balanced"}:
            return "high", 0.86
        if state in {"generated", "candidate", "validated"} and family_regime_state != "risk_off":
            return "medium", 0.68
        return "low", 0.44

    def alpha_discovery_candidates_latest(self, limit: int = 20) -> dict[str, Any]:
        registry = self._latest_registry_rows(limit=max(limit * 4, 50))
        evals_by_alpha = self._latest_by_key(self._latest_eval_rows(limit=max(limit * 4, 50)), "alpha_id")
        rankings_by_alpha = self._latest_by_key(self._latest_ranking_rows(limit=max(limit * 4, 50)), "alpha_id")
        regime = self._regime_context(limit=limit)

        items: list[dict[str, Any]] = []
        high_priority = 0
        medium_priority = 0
        low_priority = 0

        for row in registry:
            alpha_id = str(row.get("alpha_id") or "")
            state = str(row.get("state") or "candidate")
            if state in {"promoted", "retired"}:
                continue

            alpha_family = str(row.get("alpha_family") or "unknown")
            evaluation = dict(evals_by_alpha.get(alpha_id) or {})
            ranking = dict(rankings_by_alpha.get(alpha_id) or {})
            validation_decision = str(evaluation.get("decision") or "pending")
            family_regime_state = regime["family_regime_state"].get(alpha_family, "balanced")
            discovery_priority, discovery_score = self._discovery_priority(
                state=state,
                validation_decision=validation_decision,
                family_regime_state=family_regime_state,
            )

            if discovery_priority == "high":
                high_priority += 1
            elif discovery_priority == "medium":
                medium_priority += 1
            else:
                low_priority += 1

            discovery_action = "continue_research"
            if validation_decision == "pass":
                discovery_action = "prepare_for_admission_review"
            elif validation_decision == "shadow":
                discovery_action = "extend_shadow_validation"
            elif state in {"generated", "candidate", "validated"}:
                discovery_action = "run_validation"

            items.append(
                {
                    "alpha_id": alpha_id,
                    "alpha_family": alpha_family,
                    "factor_type": row.get("factor_type"),
                    "horizon": row.get("horizon"),
                    "turnover_profile": row.get("turnover_profile"),
                    "candidate_state": state,
                    "validation_decision": validation_decision,
                    "latest_summary_score": evaluation.get("summary_score"),
                    "latest_rank_score": ranking.get("rank_score"),
                    "family_regime_state": family_regime_state,
                    "discovery_priority": discovery_priority,
                    "discovery_score": round(discovery_score, 6),
                    "discovery_action": discovery_action,
                    "feature_dependencies": row.get("feature_dependencies") or [],
                }
            )

        items.sort(
            key=lambda item: (
                {"high": 0, "medium": 1, "low": 2}.get(str(item.get("discovery_priority")), 3),
                -(float(item.get("latest_rank_score") or item.get("latest_summary_score") or 0.0)),
                str(item.get("alpha_id") or ""),
            )
        )
        items = items[:limit]

        system_action = "maintain_alpha_research_backlog"
        if high_priority > 0:
            system_action = "expand_high_priority_alpha_validation"
        elif medium_priority > 0:
            system_action = "refresh_candidate_alpha_queue"

        return {
            "status": "ok",
            "current_regime": regime["current_regime"],
            "regime_confidence": regime["regime_confidence"],
            "system_regime_action": regime["system_regime_action"],
            "items": items,
            "source_packets": {
                "strategy_evolution_regime_adaptation_intelligence": "SERI-05",
                "alpha_strategy_selection_intelligence": "ASI-05",
                "research_promotion_intelligence": "RPI-06",
            },
            "alpha_discovery_candidates_summary": {
                "candidate_count": len(items),
                "high_priority_candidates": min(high_priority, len(items)),
                "medium_priority_candidates": min(medium_priority, len(items)),
                "low_priority_candidates": min(low_priority, len(items)),
                "system_alpha_discovery_action": system_action,
            },
        }

    def alpha_validation_results_latest(self, limit: int = 20) -> dict[str, Any]:
        registry_by_alpha = self._latest_by_key(self._latest_registry_rows(limit=max(limit * 4, 50)), "alpha_id")
        evals_by_alpha = self._latest_by_key(self._latest_eval_rows(limit=max(limit * 4, 50)), "alpha_id")
        experiments = self._latest_experiment_rows(limit=max(limit * 4, 50))
        experiment_by_id = {str(item.get("experiment_id") or ""): item for item in experiments}
        validations = self._latest_validation_rows(limit=max(limit * 4, 50))
        regime = self._regime_context(limit=limit)

        validation_by_alpha: dict[str, dict[str, Any]] = {}
        for row in validations:
            experiment = experiment_by_id.get(str(row.get("experiment_id") or "")) or {}
            alpha_id = str(experiment.get("alpha_id") or "")
            if alpha_id and alpha_id not in validation_by_alpha:
                validation_by_alpha[alpha_id] = row

        alpha_ids = sorted(set(list(registry_by_alpha.keys()) + list(evals_by_alpha.keys()) + list(validation_by_alpha.keys())))
        items: list[dict[str, Any]] = []
        pass_count = 0
        watch_count = 0
        fail_count = 0

        for alpha_id in alpha_ids:
            registry = dict(registry_by_alpha.get(alpha_id) or {})
            if not registry:
                continue
            alpha_family = str(registry.get("alpha_family") or "unknown")
            eval_row = dict(evals_by_alpha.get(alpha_id) or {})
            validation_row = dict(validation_by_alpha.get(alpha_id) or {})
            family_regime_state = regime["family_regime_state"].get(alpha_family, "balanced")

            summary_score = eval_row.get("summary_score")
            decision = str(eval_row.get("decision") or "pending")
            validation_source = "alpha_eval"
            if validation_row:
                summary_score = validation_row.get("summary_score", summary_score)
                validation_source = "research_factory_validation"
                passed = bool(validation_row.get("passed"))
                if passed and float(summary_score or 0.0) >= 0.8:
                    decision = "pass"
                elif passed:
                    decision = "shadow"
                else:
                    decision = "research"

            validation_status = "watch"
            if decision == "pass":
                validation_status = "pass"
                pass_count += 1
            elif decision in {"research", "reject"} or float(summary_score or 0.0) < 0.68:
                validation_status = "fail"
                fail_count += 1
            else:
                watch_count += 1

            items.append(
                {
                    "alpha_id": alpha_id,
                    "alpha_family": alpha_family,
                    "candidate_state": registry.get("state"),
                    "validation_status": validation_status,
                    "validation_decision": decision,
                    "validation_source": validation_source,
                    "summary_score": round(float(summary_score or 0.0), 6),
                    "sharpe": eval_row.get("sharpe"),
                    "max_drawdown": eval_row.get("max_drawdown"),
                    "fill_probability": eval_row.get("fill_probability"),
                    "family_regime_state": family_regime_state,
                    "validation_action": (
                        "eligible_for_admission_review"
                        if validation_status == "pass"
                        else ("continue_shadow_validation" if validation_status == "watch" else "return_to_research")
                    ),
                }
            )

        items.sort(
            key=lambda item: (
                {"pass": 0, "watch": 1, "fail": 2}.get(str(item.get("validation_status")), 3),
                -float(item.get("summary_score") or 0.0),
                str(item.get("alpha_id") or ""),
            )
        )
        items = items[:limit]

        system_action = "maintain_alpha_validation_watch"
        if pass_count > 0:
            system_action = "promote_validated_candidates_into_admission_review"
        elif fail_count > 0 and pass_count == 0:
            system_action = "refresh_validation_backlog_with_new_candidates"

        return {
            "status": "ok",
            "current_regime": regime["current_regime"],
            "regime_confidence": regime["regime_confidence"],
            "items": items,
            "source_packets": {
                "strategy_evolution_regime_adaptation_intelligence": "SERI-05",
                "research_promotion_intelligence": "RPI-06",
            },
            "alpha_validation_results_summary": {
                "validated_alpha_count": len(items),
                "pass_count": min(pass_count, len(items)),
                "watch_count": min(watch_count, len(items)),
                "fail_count": min(fail_count, len(items)),
                "system_alpha_validation_action": system_action,
            },
        }

    def alpha_admission_decision_latest(self, limit: int = 20) -> dict[str, Any]:
        validation = self.alpha_validation_results_latest(limit=max(limit * 2, 20))
        rankings_by_alpha = self._latest_by_key(self._latest_ranking_rows(limit=max(limit * 4, 50)), "alpha_id")
        lifecycle_by_alpha = self._latest_by_key(self._latest_status_rows(limit=max(limit * 4, 50)), "alpha_id")
        regime = self._regime_context(limit=limit)

        items: list[dict[str, Any]] = []
        admit_count = 0
        shadow_count = 0
        hold_count = 0
        reject_count = 0

        for item in list(validation.get("items") or []):
            alpha_id = str(item.get("alpha_id") or "")
            ranking = dict(rankings_by_alpha.get(alpha_id) or {})
            lifecycle = dict(lifecycle_by_alpha.get(alpha_id) or {})
            validation_status = str(item.get("validation_status") or "watch")
            family_regime_state = str(item.get("family_regime_state") or "balanced")
            rank_score = float(ranking.get("rank_score", 0.0) or 0.0)
            current_state = str(lifecycle.get("to_state") or item.get("candidate_state") or "candidate")

            decision = "hold"
            reason = "candidate_needs_more_evidence"

            if validation_status == "pass" and rank_score >= 0.8 and family_regime_state in {"risk_on", "balanced"}:
                decision = "admit"
                reason = "validated_candidate_is_ready_for_inventory_expansion"
                admit_count += 1
            elif validation_status in {"pass", "watch"} and rank_score >= 0.68 and family_regime_state != "risk_off":
                decision = "shadow"
                reason = "candidate_is_good_enough_for_shadow_inventory"
                shadow_count += 1
            elif validation_status == "fail" or family_regime_state == "risk_off":
                decision = "reject"
                reason = "candidate_is_not_safe_under_current_regime"
                reject_count += 1
            else:
                hold_count += 1

            items.append(
                {
                    **item,
                    "rank_score": round(rank_score, 6),
                    "current_lifecycle_state": current_state,
                    "alpha_admission_decision": decision,
                    "admission_reason": reason,
                    "admission_reason_codes": [
                        f"validation_status:{validation_status}",
                        f"rank_score:{round(rank_score, 6)}",
                        f"family_regime_state:{family_regime_state}",
                        f"current_regime:{regime['current_regime']}",
                    ],
                }
            )

        items.sort(
            key=lambda item: (
                {"admit": 0, "shadow": 1, "hold": 2, "reject": 3}.get(str(item.get("alpha_admission_decision")), 4),
                -float(item.get("rank_score") or 0.0),
                str(item.get("alpha_id") or ""),
            )
        )
        items = items[:limit]

        system_action = "maintain_alpha_admission_watch"
        if admit_count > 0:
            system_action = "admit_validated_alphas_into_inventory"
        elif shadow_count > 0:
            system_action = "expand_shadow_inventory_for_candidate_alphas"

        return {
            "status": "ok",
            "current_regime": regime["current_regime"],
            "regime_confidence": regime["regime_confidence"],
            "items": items,
            "source_packets": {
                "strategy_evolution_regime_adaptation_intelligence": "SERI-05",
                "alpha_strategy_selection_intelligence": "ASI-05",
                "research_promotion_intelligence": "RPI-06",
            },
            "alpha_admission_decision_summary": {
                "candidate_count": len(items),
                "admit_count": min(admit_count, len(items)),
                "shadow_count": min(shadow_count, len(items)),
                "hold_count": min(hold_count, len(items)),
                "reject_count": min(reject_count, len(items)),
                "system_alpha_admission_action": system_action,
            },
        }

    def alpha_lifecycle_state_latest(self, limit: int = 20) -> dict[str, Any]:
        registry_by_alpha = self._latest_by_key(self._latest_registry_rows(limit=max(limit * 4, 50)), "alpha_id")
        status_by_alpha = self._latest_by_key(self._latest_status_rows(limit=max(limit * 4, 50)), "alpha_id")
        library_by_alpha = self._latest_by_key(self._latest_library_rows(limit=max(limit * 4, 50)), "alpha_id")
        admission_by_alpha = self._latest_by_key(self.alpha_admission_decision_latest(limit=max(limit * 2, 20)).get("items") or [], "alpha_id")

        alpha_ids = sorted(set(list(registry_by_alpha.keys()) + list(status_by_alpha.keys()) + list(library_by_alpha.keys())))
        items: list[dict[str, Any]] = []
        discovery_count = 0
        validation_count = 0
        shadow_count = 0
        live_count = 0
        research_count = 0

        for alpha_id in alpha_ids:
            registry = dict(registry_by_alpha.get(alpha_id) or {})
            if not registry:
                continue
            status_row = dict(status_by_alpha.get(alpha_id) or {})
            library = dict(library_by_alpha.get(alpha_id) or {})
            admission = dict(admission_by_alpha.get(alpha_id) or {})

            lifecycle_state = str(
                library.get("state")
                or status_row.get("to_state")
                or registry.get("state")
                or "candidate"
            )

            lifecycle_stage = "discovery"
            if lifecycle_state in {"generated", "candidate"}:
                discovery_count += 1
            elif lifecycle_state in {"validated", "pass"}:
                lifecycle_stage = "validation"
                validation_count += 1
            elif lifecycle_state in {"shadow"}:
                lifecycle_stage = "shadow"
                shadow_count += 1
            elif lifecycle_state in {"promoted", "live"}:
                lifecycle_stage = "live_inventory"
                live_count += 1
            else:
                lifecycle_stage = "research"
                research_count += 1

            items.append(
                {
                    "alpha_id": alpha_id,
                    "alpha_family": registry.get("alpha_family"),
                    "current_lifecycle_state": lifecycle_state,
                    "lifecycle_stage": lifecycle_stage,
                    "latest_event_type": status_row.get("event_type"),
                    "previous_lifecycle_state": status_row.get("from_state"),
                    "lifecycle_reason": status_row.get("reason"),
                    "library_state": library.get("state"),
                    "latest_admission_decision": admission.get("alpha_admission_decision"),
                }
            )

        items.sort(
            key=lambda item: (
                {"discovery": 0, "validation": 1, "shadow": 2, "live_inventory": 3, "research": 4}.get(
                    str(item.get("lifecycle_stage")), 5
                ),
                str(item.get("alpha_id") or ""),
            )
        )
        items = items[:limit]

        system_action = "maintain_alpha_lifecycle_tracking"
        if discovery_count > live_count:
            system_action = "advance_discovery_candidates_toward_validation"
        elif live_count > 0:
            system_action = "preserve_live_alpha_inventory_while_refreshing_pipeline"

        return {
            "status": "ok",
            "items": items,
            "source_packets": {
                "research_promotion_intelligence": "RPI-06",
                "strategy_evolution_regime_adaptation_intelligence": "SERI-05",
            },
            "alpha_lifecycle_state_summary": {
                "tracked_alpha_count": len(items),
                "discovery_stage_count": min(discovery_count, len(items)),
                "validation_stage_count": min(validation_count, len(items)),
                "shadow_stage_count": min(shadow_count, len(items)),
                "live_inventory_count": min(live_count, len(items)),
                "research_stage_count": min(research_count, len(items)),
                "system_alpha_lifecycle_action": system_action,
            },
        }

    def alpha_inventory_health_latest(self, limit: int = 20) -> dict[str, Any]:
        discovery = self.alpha_discovery_candidates_latest(limit=max(limit * 2, 20))
        validation = self.alpha_validation_results_latest(limit=max(limit * 2, 20))
        admission = self.alpha_admission_decision_latest(limit=max(limit * 2, 20))
        lifecycle = self.alpha_lifecycle_state_latest(limit=max(limit * 2, 20))

        discovery_summary = discovery.get("alpha_discovery_candidates_summary") or {}
        validation_summary = validation.get("alpha_validation_results_summary") or {}
        admission_summary = admission.get("alpha_admission_decision_summary") or {}
        lifecycle_summary = lifecycle.get("alpha_lifecycle_state_summary") or {}

        candidate_count = int(discovery_summary.get("candidate_count", 0) or 0)
        pass_count = int(validation_summary.get("pass_count", 0) or 0)
        admit_count = int(admission_summary.get("admit_count", 0) or 0)
        shadow_count = int(admission_summary.get("shadow_count", 0) or 0)
        live_count = int(lifecycle_summary.get("live_inventory_count", 0) or 0)
        research_count = int(lifecycle_summary.get("research_stage_count", 0) or 0)

        replacement_pressure = "balanced"
        health_status = "healthy"
        if candidate_count <= 2 and admit_count == 0:
            replacement_pressure = "high"
            health_status = "fragile"
        elif pass_count <= 1 or research_count > live_count:
            replacement_pressure = "elevated"
            health_status = "watch"

        return {
            "status": "ok",
            "current_regime": discovery.get("current_regime"),
            "regime_confidence": discovery.get("regime_confidence"),
            "alpha_inventory_health": {
                "health_status": health_status,
                "replacement_pressure": replacement_pressure,
                "candidate_count": candidate_count,
                "validated_count": pass_count,
                "admit_count": admit_count,
                "shadow_inventory_count": shadow_count,
                "live_inventory_count": live_count,
                "research_inventory_count": research_count,
                "system_inventory_action": (
                    "accelerate_alpha_discovery_replacement"
                    if replacement_pressure == "high"
                    else ("refresh_validation_and_shadow_pipeline" if replacement_pressure == "elevated" else "maintain_alpha_inventory_health")
                ),
            },
            "source_packets": {
                "strategy_evolution_regime_adaptation_intelligence": "SERI-05",
                "alpha_strategy_selection_intelligence": "ASI-05",
                "research_promotion_intelligence": "RPI-06",
            },
        }
