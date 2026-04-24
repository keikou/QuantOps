from __future__ import annotations

import json
from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.autonomous_alpha.service import AutonomousAlphaService
from ai_hedge_bot.learning.champion_challenger import ChampionChallenger
from ai_hedge_bot.research_factory.governance_state import GovernanceStateBridge
from ai_hedge_bot.research_factory.service import ResearchFactoryService
from ai_hedge_bot.services.deployment_rollout_intelligence_service import (
    DeploymentRolloutIntelligenceService,
)
from ai_hedge_bot.services.policy_optimization_meta_control_learning_service import (
    PolicyOptimizationMetaControlLearningService,
)
from ai_hedge_bot.services.portfolio_intelligence_service import PortfolioIntelligenceService
from ai_hedge_bot.services.strategy_evolution_regime_adaptation_intelligence_service import (
    StrategyEvolutionRegimeAdaptationIntelligenceService,
)
from ai_hedge_bot.services.system_level_learning_feedback_integration_service import (
    SystemLevelLearningFeedbackIntegrationService,
)
from ai_hedge_bot.services.research_promotion_intelligence_service import (
    ResearchPromotionIntelligenceService,
)


class AutonomousAlphaExpansionStrategyGenerationIntelligenceService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.alpha_factory = AutonomousAlphaService()
        self.research_factory = ResearchFactoryService()
        self.deployment_rollout = DeploymentRolloutIntelligenceService()
        self.policy_optimization = PolicyOptimizationMetaControlLearningService()
        self.portfolio = PortfolioIntelligenceService()
        self.research_promotion = ResearchPromotionIntelligenceService()
        self.bridge = GovernanceStateBridge()
        self.champion_challenger = ChampionChallenger()
        self.strategy_evolution = StrategyEvolutionRegimeAdaptationIntelligenceService()
        self.system_learning = SystemLevelLearningFeedbackIntegrationService()

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

    def _latest_promotion_rows(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_promotions
            ORDER BY created_at DESC, alpha_id ASC
            LIMIT ?
            """,
            [max(limit, 25)],
        )
        return list(self._latest_by_key(rows, "alpha_id").values())[:limit]

    def _latest_demotion_rows(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_demotions
            ORDER BY created_at DESC, alpha_id ASC
            LIMIT ?
            """,
            [max(limit, 25)],
        )
        return list(self._latest_by_key(rows, "alpha_id").values())[:limit]

    def _latest_model_rows(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.research_factory.models.list_latest(limit=max(limit, 25))
        return list(self._latest_by_key(rows, "model_id").values())[:limit]

    def _latest_live_review_rows(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.research_factory.live_reviews.list_latest(limit=max(limit, 25))
        return list(self._latest_by_key(rows, "model_id").values())[:limit]

    def _latest_decay_rows(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.research_factory.decay_monitor.list_latest(limit=max(limit, 25))
        return list(self._latest_by_key(rows, "model_id").values())[:limit]

    def _latest_rollback_rows(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.research_factory.rollback_policy.list_latest(limit=max(limit, 25))
        return list(self._latest_by_key(rows, "model_id").values())[:limit]

    def _latest_champion_challenger_rows(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.champion_challenger.list_latest(limit=max(limit, 25))
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

    def alpha_generation_agenda_latest(self, limit: int = 20) -> dict[str, Any]:
        discovery = self.alpha_discovery_candidates_latest(limit=max(limit * 2, 20))
        inventory = self.alpha_inventory_health_latest(limit=max(limit * 2, 20))
        regime = self._regime_context(limit=limit)

        items: list[dict[str, Any]] = []
        high_count = 0
        medium_count = 0
        low_count = 0

        for item in list(discovery.get("items") or []):
            family_regime_state = str(item.get("family_regime_state") or "balanced")
            discovery_priority = str(item.get("discovery_priority") or "low")
            replacement_pressure = str((inventory.get("alpha_inventory_health") or {}).get("replacement_pressure") or "balanced")

            generation_priority = "defer"
            generation_action = "hold_generation_capacity"
            if replacement_pressure == "high" and family_regime_state != "risk_off":
                generation_priority = "expand_now"
                generation_action = "generate_and_register_new_candidates"
                high_count += 1
            elif discovery_priority in {"high", "medium"} and family_regime_state != "risk_off":
                generation_priority = "prepare"
                generation_action = "prepare_generation_designs"
                medium_count += 1
            else:
                low_count += 1

            items.append(
                {
                    "alpha_id": item.get("alpha_id"),
                    "alpha_family": item.get("alpha_family"),
                    "candidate_state": item.get("candidate_state"),
                    "family_regime_state": family_regime_state,
                    "replacement_pressure": replacement_pressure,
                    "generation_priority": generation_priority,
                    "generation_action": generation_action,
                    "generation_theme": item.get("alpha_family"),
                    "feature_dependencies": item.get("feature_dependencies") or [],
                }
            )

        items.sort(
            key=lambda item: (
                {"expand_now": 0, "prepare": 1, "defer": 2}.get(str(item.get("generation_priority")), 3),
                str(item.get("alpha_id") or ""),
            )
        )
        items = items[:limit]

        system_action = "maintain_alpha_generation_backlog"
        if high_count > 0:
            system_action = "expand_alpha_generation_now"
        elif medium_count > 0:
            system_action = "prepare_next_alpha_generation_batch"

        return {
            "status": "ok",
            "current_regime": regime["current_regime"],
            "regime_confidence": regime["regime_confidence"],
            "items": items,
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-01",
                "strategy_evolution_regime_adaptation_intelligence": "SERI-05",
            },
            "alpha_generation_agenda_summary": {
                "agenda_count": len(items),
                "expand_now_count": min(high_count, len(items)),
                "prepare_count": min(medium_count, len(items)),
                "defer_count": min(low_count, len(items)),
                "system_alpha_generation_action": system_action,
            },
        }

    def alpha_experiment_docket_latest(self, limit: int = 20) -> dict[str, Any]:
        agenda = self.alpha_generation_agenda_latest(limit=max(limit * 2, 20))
        experiments = self._latest_experiment_rows(limit=max(limit * 4, 50))
        validations = self._latest_validation_rows(limit=max(limit * 4, 50))
        validations_by_experiment = self._latest_by_key(validations, "experiment_id")
        experiment_by_alpha = self._latest_by_key(experiments, "alpha_id")

        items: list[dict[str, Any]] = []
        ready_count = 0
        active_count = 0
        blocked_count = 0

        for agenda_item in list(agenda.get("items") or []):
            alpha_id = str(agenda_item.get("alpha_id") or "")
            experiment = dict(experiment_by_alpha.get(alpha_id) or {})
            validation = dict(validations_by_experiment.get(str(experiment.get("experiment_id") or "")) or {})
            generation_priority = str(agenda_item.get("generation_priority") or "defer")
            validation_score = float(validation.get("summary_score", 0.0) or 0.0)

            experiment_status = str(experiment.get("status") or "missing")
            docket_state = "blocked"
            docket_action = "wait_for_generation"
            if experiment_status in {"generated", "tested"} and generation_priority in {"expand_now", "prepare"}:
                docket_state = "ready"
                docket_action = "run_or_refresh_experiment_validation"
                ready_count += 1
            elif experiment_status in {"generated", "tested"}:
                docket_state = "active"
                docket_action = "monitor_current_experiment"
                active_count += 1
            else:
                blocked_count += 1

            items.append(
                {
                    "alpha_id": alpha_id,
                    "alpha_family": agenda_item.get("alpha_family"),
                    "generation_priority": generation_priority,
                    "experiment_id": experiment.get("experiment_id"),
                    "experiment_status": experiment_status,
                    "validation_summary_score": round(validation_score, 6),
                    "docket_state": docket_state,
                    "docket_action": docket_action,
                }
            )

        items.sort(
            key=lambda item: (
                {"ready": 0, "active": 1, "blocked": 2}.get(str(item.get("docket_state")), 3),
                str(item.get("alpha_id") or ""),
            )
        )
        items = items[:limit]

        system_action = "maintain_alpha_experiment_docket"
        if ready_count > 0:
            system_action = "run_ready_alpha_experiments"
        elif active_count > 0:
            system_action = "monitor_active_alpha_experiments"

        return {
            "status": "ok",
            "items": items,
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-01",
                "research_promotion_intelligence": "RPI-06",
            },
            "alpha_experiment_docket_summary": {
                "docket_count": len(items),
                "ready_experiments": min(ready_count, len(items)),
                "active_experiments": min(active_count, len(items)),
                "blocked_experiments": min(blocked_count, len(items)),
                "system_alpha_experiment_action": system_action,
            },
        }

    def alpha_replacement_decision_latest(self, limit: int = 20) -> dict[str, Any]:
        admission = self.alpha_admission_decision_latest(limit=max(limit * 2, 20))
        lifecycle_by_alpha = self._latest_by_key(self.alpha_lifecycle_state_latest(limit=max(limit * 2, 20)).get("items") or [], "alpha_id")
        experiment_by_alpha = self._latest_by_key(self.alpha_experiment_docket_latest(limit=max(limit * 2, 20)).get("items") or [], "alpha_id")

        items: list[dict[str, Any]] = []
        replace_count = 0
        shadow_count = 0
        hold_count = 0
        drop_count = 0

        for item in list(admission.get("items") or []):
            alpha_id = str(item.get("alpha_id") or "")
            lifecycle = dict(lifecycle_by_alpha.get(alpha_id) or {})
            experiment = dict(experiment_by_alpha.get(alpha_id) or {})
            decision = str(item.get("alpha_admission_decision") or "hold")
            lifecycle_stage = str(lifecycle.get("lifecycle_stage") or "discovery")
            docket_state = str(experiment.get("docket_state") or "blocked")

            replacement_decision = "hold"
            replacement_reason = "candidate_is_not_ready_for_inventory_change"
            if decision == "admit" and docket_state in {"ready", "active"}:
                replacement_decision = "replace"
                replacement_reason = "validated_candidate_can_replace_fragile_inventory"
                replace_count += 1
            elif decision == "shadow":
                replacement_decision = "shadow"
                replacement_reason = "candidate_should_prove_itself_in_shadow_inventory"
                shadow_count += 1
            elif decision == "reject":
                replacement_decision = "drop"
                replacement_reason = "candidate_should_not_compete_for_inventory_slots"
                drop_count += 1
            else:
                hold_count += 1

            items.append(
                {
                    **item,
                    "lifecycle_stage": lifecycle_stage,
                    "docket_state": docket_state,
                    "alpha_replacement_decision": replacement_decision,
                    "replacement_reason": replacement_reason,
                }
            )

        items.sort(
            key=lambda item: (
                {"replace": 0, "shadow": 1, "hold": 2, "drop": 3}.get(str(item.get("alpha_replacement_decision")), 4),
                -float(item.get("rank_score") or 0.0),
                str(item.get("alpha_id") or ""),
            )
        )
        items = items[:limit]

        system_action = "maintain_alpha_replacement_watch"
        if replace_count > 0:
            system_action = "replace_fragile_alpha_inventory"
        elif shadow_count > 0:
            system_action = "expand_shadow_replacement_candidates"

        return {
            "status": "ok",
            "items": items,
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-01",
                "strategy_evolution_regime_adaptation_intelligence": "SERI-05",
            },
            "alpha_replacement_decision_summary": {
                "candidate_count": len(items),
                "replace_count": min(replace_count, len(items)),
                "shadow_count": min(shadow_count, len(items)),
                "hold_count": min(hold_count, len(items)),
                "drop_count": min(drop_count, len(items)),
                "system_alpha_replacement_action": system_action,
            },
        }

    def alpha_replacement_state_latest(self, limit: int = 20) -> dict[str, Any]:
        replacement = self.alpha_replacement_decision_latest(limit=max(limit * 2, 20))
        promotions_by_alpha = self._latest_by_key(self._latest_promotion_rows(limit=max(limit * 4, 50)), "alpha_id")
        demotions_by_alpha = self._latest_by_key(self._latest_demotion_rows(limit=max(limit * 4, 50)), "alpha_id")

        items: list[dict[str, Any]] = []
        active_count = 0
        shadow_count = 0
        pending_count = 0
        stopped_count = 0

        for item in list(replacement.get("items") or []):
            alpha_id = str(item.get("alpha_id") or "")
            promotion = dict(promotions_by_alpha.get(alpha_id) or {})
            demotion = dict(demotions_by_alpha.get(alpha_id) or {})
            replacement_decision = str(item.get("alpha_replacement_decision") or "hold")

            replacement_state = "pending"
            if replacement_decision == "replace" and promotion:
                replacement_state = "active"
                active_count += 1
            elif replacement_decision == "shadow":
                replacement_state = "shadow"
                shadow_count += 1
            elif replacement_decision == "drop" and demotion:
                replacement_state = "stopped"
                stopped_count += 1
            else:
                pending_count += 1

            items.append(
                {
                    **item,
                    "replacement_state": replacement_state,
                    "promotion_id": promotion.get("promotion_id"),
                    "demotion_id": demotion.get("demotion_id"),
                    "state_transition_note": promotion.get("notes") or demotion.get("notes") or "awaiting_next_inventory_cycle",
                }
            )

        items.sort(
            key=lambda item: (
                {"active": 0, "shadow": 1, "pending": 2, "stopped": 3}.get(str(item.get("replacement_state")), 4),
                str(item.get("alpha_id") or ""),
            )
        )
        items = items[:limit]

        system_action = "maintain_alpha_replacement_state"
        if active_count > 0:
            system_action = "track_active_alpha_replacements"
        elif shadow_count > 0:
            system_action = "monitor_shadow_replacement_candidates"

        return {
            "status": "ok",
            "items": items,
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-02",
                "research_promotion_intelligence": "RPI-06",
            },
            "alpha_replacement_state_summary": {
                "tracked_count": len(items),
                "active_replacements": min(active_count, len(items)),
                "shadow_replacements": min(shadow_count, len(items)),
                "pending_replacements": min(pending_count, len(items)),
                "stopped_replacements": min(stopped_count, len(items)),
                "system_alpha_replacement_state_action": system_action,
            },
        }

    def alpha_expansion_effectiveness_latest(self, limit: int = 20) -> dict[str, Any]:
        generation = self.alpha_generation_agenda_latest(limit=max(limit * 2, 20))
        replacement = self.alpha_replacement_decision_latest(limit=max(limit * 2, 20))
        replacement_state = self.alpha_replacement_state_latest(limit=max(limit * 2, 20))
        inventory = self.alpha_inventory_health_latest(limit=max(limit * 2, 20))

        generation_summary = generation.get("alpha_generation_agenda_summary") or {}
        replacement_summary = replacement.get("alpha_replacement_decision_summary") or {}
        state_summary = replacement_state.get("alpha_replacement_state_summary") or {}
        health = inventory.get("alpha_inventory_health") or {}

        expansion_status = "effective"
        if int(replacement_summary.get("replace_count", 0) or 0) == 0 and str(health.get("replacement_pressure") or "") == "high":
            expansion_status = "insufficient"
        elif int(state_summary.get("pending_replacements", 0) or 0) > int(state_summary.get("active_replacements", 0) or 0):
            expansion_status = "watch"

        return {
            "status": "ok",
            "alpha_expansion_effectiveness": {
                "expansion_status": expansion_status,
                "generation_ready_count": int(generation_summary.get("expand_now_count", 0) or 0),
                "replacement_ready_count": int(replacement_summary.get("replace_count", 0) or 0),
                "active_replacement_count": int(state_summary.get("active_replacements", 0) or 0),
                "shadow_replacement_count": int(state_summary.get("shadow_replacements", 0) or 0),
                "replacement_pressure": health.get("replacement_pressure"),
                "system_alpha_expansion_action": (
                    "accelerate_alpha_expansion_replacement"
                    if expansion_status == "insufficient"
                    else ("clear_pending_alpha_replacements" if expansion_status == "watch" else "maintain_alpha_expansion_effectiveness")
                ),
            },
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-02",
                "research_promotion_intelligence": "RPI-06",
                "strategy_evolution_regime_adaptation_intelligence": "SERI-05",
            },
        }

    def alpha_runtime_deployment_candidates_latest(self, limit: int = 20) -> dict[str, Any]:
        replacement = self.alpha_replacement_decision_latest(limit=max(limit * 2, 20))
        rollout = self.deployment_rollout.candidate_docket_latest(limit=max(limit * 2, 20))
        models = self._latest_model_rows(limit=max(limit * 4, 50))

        rollout_by_family = self._latest_by_key(list(rollout.get("items") or []), "alpha_family")
        model_by_alpha: dict[str, dict[str, Any]] = {}
        experiments = self._latest_experiment_rows(limit=max(limit * 4, 50))
        experiment_by_alpha = self._latest_by_key(experiments, "alpha_id")
        model_by_experiment = self._latest_by_key(models, "experiment_id")
        for alpha_id, experiment in experiment_by_alpha.items():
            model = model_by_experiment.get(str(experiment.get("experiment_id") or ""))
            if model:
                model_by_alpha[alpha_id] = model

        items: list[dict[str, Any]] = []
        ready_count = 0
        shadow_count = 0
        blocked_count = 0

        for item in list(replacement.get("items") or []):
            alpha_id = str(item.get("alpha_id") or "")
            alpha_family = str(item.get("alpha_family") or "unknown")
            rollout_item = dict(rollout_by_family.get(alpha_family) or {})
            model = dict(model_by_alpha.get(alpha_id) or {})
            replacement_decision = str(item.get("alpha_replacement_decision") or "hold")
            approval_status = str(rollout_item.get("approval_status") or "pending_evidence")

            deployment_candidate_status = "shadow"
            runtime_deployment_action = "keep_in_shadow"
            if replacement_decision == "replace" and approval_status == "ready_for_review":
                deployment_candidate_status = "ready"
                runtime_deployment_action = str(rollout_item.get("deployment_action") or "prepare_limited_rollout")
                ready_count += 1
            elif replacement_decision == "shadow":
                shadow_count += 1
            else:
                deployment_candidate_status = "blocked"
                runtime_deployment_action = "hold_runtime_deployment"
                blocked_count += 1

            items.append(
                {
                    **item,
                    "model_id": model.get("model_id"),
                    "model_state": model.get("state"),
                    "deployment_candidate_status": deployment_candidate_status,
                    "recommended_rollout_stage": rollout_item.get("recommended_rollout_stage"),
                    "approval_status": approval_status,
                    "runtime_deployment_action": runtime_deployment_action,
                    "rollout_priority": rollout_item.get("rollout_priority"),
                }
            )

        items.sort(
            key=lambda item: (
                {"ready": 0, "shadow": 1, "blocked": 2}.get(str(item.get("deployment_candidate_status")), 3),
                str(item.get("alpha_id") or ""),
            )
        )
        items = items[:limit]

        system_action = "maintain_runtime_alpha_shadow_inventory"
        if ready_count > 0:
            system_action = "prepare_runtime_deployment_for_replacement_alphas"
        elif shadow_count > 0:
            system_action = "continue_shadow_runtime_evidence_collection"

        return {
            "status": "ok",
            "items": items,
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-02",
                "deployment_rollout_intelligence": "DRI-05",
            },
            "alpha_runtime_deployment_candidates_summary": {
                "candidate_count": len(items),
                "ready_candidates": min(ready_count, len(items)),
                "shadow_candidates": min(shadow_count, len(items)),
                "blocked_candidates": min(blocked_count, len(items)),
                "system_alpha_runtime_deployment_action": system_action,
            },
        }

    def alpha_runtime_governance_feedback_latest(self, limit: int = 20) -> dict[str, Any]:
        deployment = self.alpha_runtime_deployment_candidates_latest(limit=max(limit * 2, 20))
        reviews_by_model = self._latest_by_key(self._latest_live_review_rows(limit=max(limit * 4, 50)), "model_id")
        decay_by_model = self._latest_by_key(self._latest_decay_rows(limit=max(limit * 4, 50)), "model_id")

        items: list[dict[str, Any]] = []
        healthy_count = 0
        watch_count = 0
        intervention_count = 0

        for item in list(deployment.get("items") or []):
            model_id = str(item.get("model_id") or "")
            review = dict(reviews_by_model.get(model_id) or {})
            decay = dict(decay_by_model.get(model_id) or {})
            review_decision = str(review.get("decision") or "keep")
            decay_status = str(decay.get("status") or "monitor")

            runtime_feedback_status = "healthy"
            runtime_feedback_action = "keep_runtime_candidate_on_track"
            if review_decision == "rollback" or decay_status == "demote_candidate":
                runtime_feedback_status = "intervention_required"
                runtime_feedback_action = "prepare_runtime_rollback"
                intervention_count += 1
            elif review_decision in {"reduce_capital", "shadow"} or decay_status == "review_required":
                runtime_feedback_status = "watch"
                runtime_feedback_action = "tighten_runtime_review_watch"
                watch_count += 1
            else:
                healthy_count += 1

            items.append(
                {
                    **item,
                    "live_review_decision": review_decision,
                    "live_review_flags": review.get("flags") or [],
                    "alpha_decay_severity": decay.get("severity"),
                    "alpha_decay_status": decay_status,
                    "runtime_feedback_status": runtime_feedback_status,
                    "runtime_feedback_action": runtime_feedback_action,
                }
            )

        items.sort(
            key=lambda item: (
                {"intervention_required": 0, "watch": 1, "healthy": 2}.get(str(item.get("runtime_feedback_status")), 3),
                str(item.get("alpha_id") or ""),
            )
        )
        items = items[:limit]

        system_action = "maintain_runtime_feedback_watch"
        if intervention_count > 0:
            system_action = "prepare_runtime_intervention_for_alpha_candidates"
        elif watch_count > 0:
            system_action = "monitor_runtime_feedback_drift"

        return {
            "status": "ok",
            "items": items,
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-03",
                "research_promotion_intelligence": "RPI-06",
            },
            "alpha_runtime_governance_feedback_summary": {
                "candidate_count": len(items),
                "healthy_candidates": min(healthy_count, len(items)),
                "watch_candidates": min(watch_count, len(items)),
                "intervention_required_candidates": min(intervention_count, len(items)),
                "system_alpha_runtime_feedback_action": system_action,
            },
        }

    def alpha_runtime_rollback_response_latest(self, limit: int = 20) -> dict[str, Any]:
        feedback = self.alpha_runtime_governance_feedback_latest(limit=max(limit * 2, 20))
        rollback_by_model = self._latest_by_key(self._latest_rollback_rows(limit=max(limit * 4, 50)), "model_id")

        items: list[dict[str, Any]] = []
        rollback_count = 0
        reduce_count = 0
        hold_count = 0

        for item in list(feedback.get("items") or []):
            model_id = str(item.get("model_id") or "")
            rollback = dict(rollback_by_model.get(model_id) or {})
            runtime_feedback_status = str(item.get("runtime_feedback_status") or "healthy")
            rollback_action = str(rollback.get("action") or "hold")

            runtime_rollback_response = "hold"
            runtime_rollback_reason = "runtime_candidate_remains_acceptable"
            if rollback_action == "rollback" or runtime_feedback_status == "intervention_required":
                runtime_rollback_response = "rollback"
                runtime_rollback_reason = "runtime_feedback_or_decay_requires_rollback"
                rollback_count += 1
            elif str(item.get("live_review_decision") or "") == "reduce_capital":
                runtime_rollback_response = "reduce"
                runtime_rollback_reason = "candidate_should_trade_with_reduced_runtime_risk"
                reduce_count += 1
            else:
                hold_count += 1

            items.append(
                {
                    **item,
                    "trigger_reason": rollback.get("trigger_reason"),
                    "selected_model_id": rollback.get("selected_model_id"),
                    "runtime_rollback_response": runtime_rollback_response,
                    "runtime_rollback_reason": runtime_rollback_reason,
                }
            )

        items.sort(
            key=lambda item: (
                {"rollback": 0, "reduce": 1, "hold": 2}.get(str(item.get("runtime_rollback_response")), 3),
                str(item.get("alpha_id") or ""),
            )
        )
        items = items[:limit]

        system_action = "hold_runtime_alpha_candidates"
        if rollback_count > 0:
            system_action = "rollback_runtime_alpha_candidates_under_stress"
        elif reduce_count > 0:
            system_action = "reduce_runtime_alpha_candidate_risk"

        return {
            "status": "ok",
            "items": items,
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-03",
                "research_promotion_intelligence": "RPI-06",
            },
            "alpha_runtime_rollback_response_summary": {
                "candidate_count": len(items),
                "rollback_candidates": min(rollback_count, len(items)),
                "reduce_candidates": min(reduce_count, len(items)),
                "hold_candidates": min(hold_count, len(items)),
                "system_alpha_runtime_rollback_action": system_action,
            },
        }

    def alpha_runtime_champion_challenger_latest(self, limit: int = 20) -> dict[str, Any]:
        replacement = self.alpha_runtime_rollback_response_latest(limit=max(limit * 2, 20))
        cc_runs = self._latest_champion_challenger_rows(limit=max(limit, 10))
        latest_cc = dict(cc_runs[0] if cc_runs else {})
        champion_alpha_id = self.bridge.alpha_id_for_model(str(latest_cc.get("champion_model_id") or "")) if latest_cc else None
        challenger_alpha_id = self.bridge.alpha_id_for_model(str(latest_cc.get("challenger_model_id") or "")) if latest_cc else None

        items: list[dict[str, Any]] = []
        switch_count = 0
        keep_count = 0

        for item in list(replacement.get("items") or []):
            alpha_id = str(item.get("alpha_id") or "")
            champion_role = "observer"
            runtime_competition_action = "hold_current_runtime_posture"
            if alpha_id and alpha_id == challenger_alpha_id and str(latest_cc.get("recommended_action") or "") == "switch_live":
                champion_role = "challenger_winner"
                runtime_competition_action = "switch_runtime_to_challenger"
                switch_count += 1
            elif alpha_id and alpha_id == champion_alpha_id:
                champion_role = "current_champion"
                runtime_competition_action = "keep_runtime_champion_live"
                keep_count += 1

            items.append(
                {
                    **item,
                    "champion_model_id": latest_cc.get("champion_model_id"),
                    "challenger_model_id": latest_cc.get("challenger_model_id"),
                    "winner": latest_cc.get("winner"),
                    "recommended_action": latest_cc.get("recommended_action"),
                    "capital_shift": latest_cc.get("capital_shift"),
                    "runtime_competition_role": champion_role,
                    "runtime_competition_action": runtime_competition_action,
                }
            )

        items = items[:limit]
        system_action = "maintain_current_runtime_winner"
        if switch_count > 0:
            system_action = "switch_runtime_to_challenger_winner"
        elif keep_count > 0:
            system_action = "preserve_runtime_champion"

        return {
            "status": "ok",
            "items": items,
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-03",
                "research_promotion_intelligence": "RPI-06",
            },
            "alpha_runtime_champion_challenger_summary": {
                "candidate_count": len(items),
                "switch_candidates": min(switch_count, len(items)),
                "keep_candidates": min(keep_count, len(items)),
                "system_alpha_runtime_competition_action": system_action,
            },
        }

    def alpha_runtime_expansion_effectiveness_latest(self, limit: int = 20) -> dict[str, Any]:
        deployment = self.alpha_runtime_deployment_candidates_latest(limit=max(limit * 2, 20))
        feedback = self.alpha_runtime_governance_feedback_latest(limit=max(limit * 2, 20))
        rollback = self.alpha_runtime_rollback_response_latest(limit=max(limit * 2, 20))
        champion = self.alpha_runtime_champion_challenger_latest(limit=max(limit * 2, 20))

        deployment_summary = deployment.get("alpha_runtime_deployment_candidates_summary") or {}
        feedback_summary = feedback.get("alpha_runtime_governance_feedback_summary") or {}
        rollback_summary = rollback.get("alpha_runtime_rollback_response_summary") or {}
        champion_summary = champion.get("alpha_runtime_champion_challenger_summary") or {}

        effectiveness_status = "effective"
        if int(rollback_summary.get("rollback_candidates", 0) or 0) > 0:
            effectiveness_status = "fragile"
        elif int(feedback_summary.get("watch_candidates", 0) or 0) > int(feedback_summary.get("healthy_candidates", 0) or 0):
            effectiveness_status = "watch"

        return {
            "status": "ok",
            "alpha_runtime_expansion_effectiveness": {
                "effectiveness_status": effectiveness_status,
                "deployment_ready_count": int(deployment_summary.get("ready_candidates", 0) or 0),
                "healthy_runtime_count": int(feedback_summary.get("healthy_candidates", 0) or 0),
                "rollback_runtime_count": int(rollback_summary.get("rollback_candidates", 0) or 0),
                "switch_runtime_count": int(champion_summary.get("switch_candidates", 0) or 0),
                "system_alpha_runtime_expansion_action": (
                    "stabilize_runtime_alpha_expansion"
                    if effectiveness_status == "fragile"
                    else ("monitor_runtime_alpha_expansion_drift" if effectiveness_status == "watch" else "maintain_runtime_alpha_expansion")
                ),
            },
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-03",
                "deployment_rollout_intelligence": "DRI-05",
                "research_promotion_intelligence": "RPI-06",
            },
        }

    @staticmethod
    def _family_latest(rows: list[dict[str, Any]], family_key: str = "alpha_family") -> dict[str, dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for row in rows:
            family = str(row.get(family_key) or "unknown")
            if family not in latest:
                latest[family] = row
        return latest

    def alpha_next_cycle_learning_input_latest(self, limit: int = 20) -> dict[str, Any]:
        feedback = self.alpha_runtime_governance_feedback_latest(limit=max(limit * 2, 20))
        rollback = self.alpha_runtime_rollback_response_latest(limit=max(limit * 2, 20))
        champion = self.alpha_runtime_champion_challenger_latest(limit=max(limit * 2, 20))
        learning = self.system_learning.policy_updates_latest(limit=max(limit * 2, 20))

        feedback_by_family = self._family_latest(list(feedback.get("items") or []))
        rollback_by_family = self._family_latest(list(rollback.get("items") or []))
        champion_by_family = self._family_latest(list(champion.get("items") or []))
        learning_by_family = self._family_latest(list(learning.get("items") or []))

        families = sorted(
            set(feedback_by_family.keys())
            | set(rollback_by_family.keys())
            | set(champion_by_family.keys())
            | set(learning_by_family.keys())
        )

        items: list[dict[str, Any]] = []
        reinforce_count = 0
        caution_count = 0
        rebalance_count = 0
        observe_count = 0

        for family in families:
            feedback_item = dict(feedback_by_family.get(family) or {})
            rollback_item = dict(rollback_by_family.get(family) or {})
            champion_item = dict(champion_by_family.get(family) or {})
            learning_item = dict(learning_by_family.get(family) or {})

            runtime_feedback_status = str(feedback_item.get("runtime_feedback_status") or "healthy")
            runtime_rollback_response = str(rollback_item.get("runtime_rollback_response") or "hold")
            learning_action = str(learning_item.get("learning_action") or "observe")
            competition_action = str(champion_item.get("runtime_competition_action") or "hold_current_runtime_posture")

            next_cycle_learning_input = "observe"
            reason_codes: list[str] = []
            if runtime_feedback_status == "intervention_required" or runtime_rollback_response == "rollback":
                next_cycle_learning_input = "caution"
                reason_codes.append("runtime_intervention_or_rollback_present")
            elif runtime_feedback_status == "watch" or runtime_rollback_response == "reduce":
                next_cycle_learning_input = "rebalance"
                reason_codes.append("runtime_watch_or_reduce_present")
            elif learning_action == "reinforce" and competition_action != "switch_runtime_to_challenger":
                next_cycle_learning_input = "reinforce"
                reason_codes.append("runtime_feedback_supports_positive_learning")
            elif learning_action in {"caution", "rebalance"}:
                next_cycle_learning_input = learning_action
                reason_codes.append("existing_learning_signal_retained")
            else:
                reason_codes.append("collect_more_alpha_runtime_feedback")

            if str(champion_item.get("runtime_competition_role") or "") == "challenger_winner":
                reason_codes.append("challenger_winner_should_shape_next_cycle")
            elif str(champion_item.get("runtime_competition_role") or "") == "current_champion":
                reason_codes.append("champion_posture_remains_reference")

            if next_cycle_learning_input == "reinforce":
                reinforce_count += 1
            elif next_cycle_learning_input == "caution":
                caution_count += 1
            elif next_cycle_learning_input == "rebalance":
                rebalance_count += 1
            else:
                observe_count += 1

            items.append(
                {
                    "alpha_family": family,
                    "runtime_feedback_status": runtime_feedback_status,
                    "runtime_rollback_response": runtime_rollback_response,
                    "runtime_competition_role": champion_item.get("runtime_competition_role"),
                    "runtime_competition_action": competition_action,
                    "learning_action": learning_action,
                    "selection_score_adjustment": float(learning_item.get("selection_score_adjustment", 0.0) or 0.0),
                    "capital_multiplier_adjustment": float(learning_item.get("capital_multiplier_adjustment", 1.0) or 1.0),
                    "review_pressure": learning_item.get("review_pressure"),
                    "runtime_caution": learning_item.get("runtime_caution"),
                    "next_cycle_learning_input": next_cycle_learning_input,
                    "next_cycle_learning_reason_codes": reason_codes,
                }
            )

        system_action = "collect_more_alpha_runtime_learning"
        if caution_count > 0:
            system_action = "tighten_next_cycle_learning_for_fragile_families"
        elif rebalance_count > 0:
            system_action = "rebalance_next_cycle_learning_inputs"
        elif reinforce_count > 0:
            system_action = "reinforce_next_cycle_learning_for_successful_families"

        return {
            "status": "ok",
            "items": items[:limit],
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-04",
                "system_level_learning_feedback_integration": "SLLFI-05",
                "strategy_evolution_regime_adaptation_intelligence": "SERI-05",
            },
            "alpha_next_cycle_learning_input_summary": {
                "family_count": min(len(items), limit),
                "reinforce_inputs": min(reinforce_count, len(items[:limit])),
                "caution_inputs": min(caution_count, len(items[:limit])),
                "rebalance_inputs": min(rebalance_count, len(items[:limit])),
                "observe_inputs": min(observe_count, len(items[:limit])),
                "system_alpha_next_cycle_learning_action": system_action,
            },
        }

    def alpha_next_cycle_policy_bridge_latest(self, limit: int = 20) -> dict[str, Any]:
        learning_input = self.alpha_next_cycle_learning_input_latest(limit=max(limit * 2, 20))
        learning_policy = self.system_learning.policy_updates_latest(limit=max(limit * 2, 20))
        policy_by_family = self._family_latest(list(learning_policy.get("items") or []))

        items: list[dict[str, Any]] = []
        expand_count = 0
        constrain_count = 0
        rebalance_count = 0
        hold_count = 0

        for item in list(learning_input.get("items") or []):
            family = str(item.get("alpha_family") or "unknown")
            policy_item = dict(policy_by_family.get(family) or {})
            next_cycle_learning_input = str(item.get("next_cycle_learning_input") or "observe")

            policy_bridge_state = "hold"
            expansion_policy_bias = "neutral"
            if next_cycle_learning_input == "caution":
                policy_bridge_state = "constrain"
                expansion_policy_bias = "constrain"
                constrain_count += 1
            elif next_cycle_learning_input == "rebalance":
                policy_bridge_state = "rebalance"
                expansion_policy_bias = "mixed"
                rebalance_count += 1
            elif next_cycle_learning_input == "reinforce":
                policy_bridge_state = "expand"
                expansion_policy_bias = "expand"
                expand_count += 1
            else:
                hold_count += 1

            items.append(
                {
                    **item,
                    "policy_bridge_state": policy_bridge_state,
                    "expansion_policy_bias": expansion_policy_bias,
                    "selection_score_adjustment": float(
                        policy_item.get("selection_score_adjustment", item.get("selection_score_adjustment", 0.0)) or 0.0
                    ),
                    "capital_multiplier_adjustment": float(
                        policy_item.get("capital_multiplier_adjustment", item.get("capital_multiplier_adjustment", 1.0)) or 1.0
                    ),
                    "review_pressure": policy_item.get("review_pressure", item.get("review_pressure")),
                    "runtime_caution": policy_item.get("runtime_caution", item.get("runtime_caution")),
                    "policy_update_reason_codes": policy_item.get("policy_update_reason_codes")
                    or item.get("next_cycle_learning_reason_codes")
                    or [],
                }
            )

        system_action = "hold_current_alpha_policy_bridge"
        if constrain_count > 0:
            system_action = "constrain_alpha_expansion_policy_for_fragile_families"
        elif rebalance_count > 0:
            system_action = "rebalance_alpha_expansion_policy_across_families"
        elif expand_count > 0:
            system_action = "expand_alpha_policy_support_for_successful_families"

        return {
            "status": "ok",
            "items": items[:limit],
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-04",
                "system_level_learning_feedback_integration": "SLLFI-05",
            },
            "alpha_next_cycle_policy_bridge_summary": {
                "family_count": min(len(items), limit),
                "expand_families": min(expand_count, len(items[:limit])),
                "constrain_families": min(constrain_count, len(items[:limit])),
                "rebalance_families": min(rebalance_count, len(items[:limit])),
                "hold_families": min(hold_count, len(items[:limit])),
                "system_alpha_policy_bridge_action": system_action,
            },
        }

    def alpha_regime_adaptation_input_latest(self, limit: int = 20) -> dict[str, Any]:
        policy_bridge = self.alpha_next_cycle_policy_bridge_latest(limit=max(limit * 2, 20))
        regime = self.strategy_evolution.strategy_gating_decision_latest(limit=max(limit * 2, 20))
        regime_by_family = self._family_latest(list(regime.get("items") or []))

        items: list[dict[str, Any]] = []
        expand_count = 0
        watch_count = 0
        prune_count = 0

        for item in list(policy_bridge.get("items") or []):
            family = str(item.get("alpha_family") or "unknown")
            regime_item = dict(regime_by_family.get(family) or {})
            policy_bridge_state = str(item.get("policy_bridge_state") or "hold")
            gating_decision = str(regime_item.get("strategy_gating_decision") or "shadow")
            family_regime_state = str(regime_item.get("family_regime_state") or "balanced")

            regime_adaptation_input = "watch"
            if gating_decision in {"gate", "retire"} or policy_bridge_state == "constrain":
                regime_adaptation_input = "prune"
                prune_count += 1
            elif gating_decision == "allow" and policy_bridge_state == "expand" and family_regime_state == "risk_on":
                regime_adaptation_input = "expand"
                expand_count += 1
            else:
                watch_count += 1

            items.append(
                {
                    **item,
                    "current_regime": regime.get("current_regime"),
                    "family_regime_state": family_regime_state,
                    "strategy_gating_decision": gating_decision,
                    "system_regime_action": regime.get("system_regime_action"),
                    "regime_adaptation_input": regime_adaptation_input,
                    "regime_adaptation_reason_codes": [
                        f"policy_bridge_state:{policy_bridge_state}",
                        f"family_regime_state:{family_regime_state}",
                        f"strategy_gating_decision:{gating_decision}",
                    ],
                }
            )

        system_action = "observe_alpha_regime_adaptation_inputs"
        if prune_count > 0:
            system_action = "prune_alpha_expansion_under_regime_stress"
        elif expand_count > 0:
            system_action = "expand_alpha_families_aligned_with_current_regime"

        return {
            "status": "ok",
            "current_regime": regime.get("current_regime"),
            "regime_confidence": regime.get("regime_confidence"),
            "items": items[:limit],
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-04",
                "strategy_evolution_regime_adaptation_intelligence": "SERI-05",
                "system_level_learning_feedback_integration": "SLLFI-05",
            },
            "alpha_regime_adaptation_input_summary": {
                "family_count": min(len(items), limit),
                "expand_inputs": min(expand_count, len(items[:limit])),
                "watch_inputs": min(watch_count, len(items[:limit])),
                "prune_inputs": min(prune_count, len(items[:limit])),
                "system_alpha_regime_adaptation_action": system_action,
            },
        }

    def alpha_universe_refresh_priorities_latest(self, limit: int = 20) -> dict[str, Any]:
        regime_input = self.alpha_regime_adaptation_input_latest(limit=max(limit * 2, 20))
        discovery = self.alpha_discovery_candidates_latest(limit=max(limit * 3, 30))
        generation = self.alpha_generation_agenda_latest(limit=max(limit * 3, 30))

        discovery_by_family = self._family_latest(list(discovery.get("items") or []))
        generation_by_family = self._family_latest(list(generation.get("items") or []))

        items: list[dict[str, Any]] = []
        expand_count = 0
        replace_count = 0
        hold_count = 0
        prune_count = 0

        for item in list(regime_input.get("items") or []):
            family = str(item.get("alpha_family") or "unknown")
            discovery_item = dict(discovery_by_family.get(family) or {})
            generation_item = dict(generation_by_family.get(family) or {})
            regime_adaptation_input = str(item.get("regime_adaptation_input") or "watch")
            discovery_priority = str(discovery_item.get("discovery_priority") or "low")
            generation_action = str(generation_item.get("generation_action") or "hold_generation_capacity")

            universe_refresh_priority = "hold"
            universe_refresh_action = "hold_family_universe"
            if regime_adaptation_input == "prune":
                universe_refresh_priority = "prune"
                universe_refresh_action = "prune_or_replace_fragile_family_capacity"
                prune_count += 1
            elif regime_adaptation_input == "expand" and discovery_priority == "high":
                universe_refresh_priority = "expand"
                universe_refresh_action = "expand_family_with_validated_candidates"
                expand_count += 1
            elif generation_action == "expand_generation_now":
                universe_refresh_priority = "replace"
                universe_refresh_action = "refresh_family_generation_and_replacement_queue"
                replace_count += 1
            else:
                hold_count += 1

            items.append(
                {
                    **item,
                    "discovery_priority": discovery_priority,
                    "generation_action": generation_action,
                    "universe_refresh_priority": universe_refresh_priority,
                    "universe_refresh_action": universe_refresh_action,
                }
            )

        system_action = "maintain_alpha_universe_refresh_backlog"
        if prune_count > 0:
            system_action = "prune_fragile_alpha_families_and_refresh_capacity"
        elif expand_count > 0:
            system_action = "expand_alpha_universe_in_supportive_families"
        elif replace_count > 0:
            system_action = "refresh_alpha_universe_with_new_generation"

        return {
            "status": "ok",
            "current_regime": regime_input.get("current_regime"),
            "regime_confidence": regime_input.get("regime_confidence"),
            "items": items[:limit],
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-04",
                "strategy_evolution_regime_adaptation_intelligence": "SERI-05",
                "system_level_learning_feedback_integration": "SLLFI-05",
            },
            "alpha_universe_refresh_priorities_summary": {
                "family_count": min(len(items), limit),
                "expand_priorities": min(expand_count, len(items[:limit])),
                "replace_priorities": min(replace_count, len(items[:limit])),
                "hold_priorities": min(hold_count, len(items[:limit])),
                "prune_priorities": min(prune_count, len(items[:limit])),
                "system_alpha_universe_refresh_action": system_action,
            },
        }

    def alpha_expansion_learning_effectiveness_latest(self, limit: int = 20) -> dict[str, Any]:
        learning_input = self.alpha_next_cycle_learning_input_latest(limit=max(limit * 2, 20))
        policy_bridge = self.alpha_next_cycle_policy_bridge_latest(limit=max(limit * 2, 20))
        regime_input = self.alpha_regime_adaptation_input_latest(limit=max(limit * 2, 20))
        universe = self.alpha_universe_refresh_priorities_latest(limit=max(limit * 2, 20))

        learning_summary = learning_input.get("alpha_next_cycle_learning_input_summary") or {}
        policy_summary = policy_bridge.get("alpha_next_cycle_policy_bridge_summary") or {}
        regime_summary = regime_input.get("alpha_regime_adaptation_input_summary") or {}
        universe_summary = universe.get("alpha_universe_refresh_priorities_summary") or {}

        effectiveness_status = "closed_loop_ready"
        if int(regime_summary.get("prune_inputs", 0) or 0) > 0:
            effectiveness_status = "fragile"
        elif int(policy_summary.get("rebalance_families", 0) or 0) > 0 or int(learning_summary.get("rebalance_inputs", 0) or 0) > 0:
            effectiveness_status = "watch"

        return {
            "status": "ok",
            "alpha_expansion_learning_effectiveness": {
                "effectiveness_status": effectiveness_status,
                "reinforce_input_count": int(learning_summary.get("reinforce_inputs", 0) or 0),
                "constrain_policy_count": int(policy_summary.get("constrain_families", 0) or 0),
                "prune_regime_count": int(regime_summary.get("prune_inputs", 0) or 0),
                "expand_universe_count": int(universe_summary.get("expand_priorities", 0) or 0),
                "replace_universe_count": int(universe_summary.get("replace_priorities", 0) or 0),
                "system_alpha_expansion_learning_action": (
                    "stabilize_alpha_expansion_before_next_cycle"
                    if effectiveness_status == "fragile"
                    else (
                        "monitor_alpha_expansion_learning_bridge"
                        if effectiveness_status == "watch"
                        else "apply_alpha_expansion_closed_loop_learning"
                    )
                ),
            },
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-04",
                "system_level_learning_feedback_integration": "SLLFI-05",
                "strategy_evolution_regime_adaptation_intelligence": "SERI-05",
            },
        }

    def alpha_promotion_bridge_latest(self, limit: int = 20) -> dict[str, Any]:
        universe = self.alpha_universe_refresh_priorities_latest(limit=max(limit * 2, 20))
        promotion = self.research_promotion.promotion_agenda_latest(limit=max(limit * 3, 30))

        universe_by_family = self._family_latest(list(universe.get("items") or []))
        items: list[dict[str, Any]] = []
        accelerate_count = 0
        hold_count = 0
        retire_count = 0

        for item in list(promotion.get("items") or []):
            family = str(item.get("alpha_family") or "unknown")
            universe_item = dict(universe_by_family.get(family) or {})
            universe_refresh_priority = str(universe_item.get("universe_refresh_priority") or "hold")
            promotion_action = str(item.get("promotion_action") or "stay_queued")

            bridge_status = "hold"
            bridge_action = "hold_alpha_in_review_backlog"
            if universe_refresh_priority == "expand" and promotion_action in {"promote", "advance"}:
                bridge_status = "accelerate"
                bridge_action = "accelerate_alpha_promotion_review"
                accelerate_count += 1
            elif universe_refresh_priority == "prune" and promotion_action in {"demote", "retire"}:
                bridge_status = "retire"
                bridge_action = "accelerate_alpha_exit_review"
                retire_count += 1
            else:
                hold_count += 1

            items.append(
                {
                    **item,
                    "universe_refresh_priority": universe_refresh_priority,
                    "universe_refresh_action": universe_item.get("universe_refresh_action"),
                    "promotion_bridge_status": bridge_status,
                    "promotion_bridge_action": bridge_action,
                }
            )

        items.sort(
            key=lambda item: (
                {"accelerate": 0, "retire": 1, "hold": 2}.get(str(item.get("promotion_bridge_status")), 3),
                {"immediate": 0, "high": 1, "normal": 2, "low": 3}.get(str(item.get("review_priority")), 4),
                -float(item.get("selection_score", 0.0) or 0.0),
                str(item.get("alpha_id") or ""),
            )
        )
        items = items[:limit]

        system_action = "hold_alpha_promotion_bridge"
        if accelerate_count > 0:
            system_action = "accelerate_alpha_promotion_for_expansion_families"
        elif retire_count > 0:
            system_action = "accelerate_alpha_exit_for_pruned_families"

        return {
            "status": "ok",
            "items": items,
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-05",
                "research_promotion_intelligence": "RPI-06",
            },
            "alpha_promotion_bridge_summary": {
                "alpha_count": len(items),
                "accelerate_candidates": sum(1 for item in items if item.get("promotion_bridge_status") == "accelerate"),
                "hold_candidates": sum(1 for item in items if item.get("promotion_bridge_status") == "hold"),
                "retire_candidates": sum(1 for item in items if item.get("promotion_bridge_status") == "retire"),
                "system_alpha_promotion_bridge_action": system_action,
            },
        }

    def alpha_family_capital_intent_latest(self, limit: int = 20) -> dict[str, Any]:
        policy_bridge = self.alpha_next_cycle_policy_bridge_latest(limit=max(limit * 2, 20))
        policy_effectiveness = self.policy_optimization.outcome_effectiveness_latest(limit=max(limit * 2, 20))
        universe = self.alpha_universe_refresh_priorities_latest(limit=max(limit * 2, 20))

        policy_effectiveness_by_family = self._family_latest(list(policy_effectiveness.get("items") or []))
        universe_by_family = self._family_latest(list(universe.get("items") or []))
        items: list[dict[str, Any]] = []
        expand_count = 0
        constrain_count = 0
        hold_count = 0

        for item in list(policy_bridge.get("items") or []):
            family = str(item.get("alpha_family") or "unknown")
            policy_item = dict(policy_effectiveness_by_family.get(family) or {})
            universe_item = dict(universe_by_family.get(family) or {})
            policy_bridge_state = str(item.get("policy_bridge_state") or "hold")
            realized_effect = str(policy_item.get("realized_effect") or "neutral")
            universe_refresh_priority = str(universe_item.get("universe_refresh_priority") or "hold")

            capital_intent = "hold"
            target_family_multiplier = float(item.get("capital_multiplier_adjustment", 1.0) or 1.0)
            if policy_bridge_state == "expand" and realized_effect == "beneficial" and universe_refresh_priority == "expand":
                capital_intent = "expand"
                target_family_multiplier = max(target_family_multiplier, 1.15)
                expand_count += 1
            elif policy_bridge_state == "constrain" or universe_refresh_priority == "prune":
                capital_intent = "constrain"
                target_family_multiplier = min(target_family_multiplier, 0.8)
                constrain_count += 1
            else:
                hold_count += 1

            items.append(
                {
                    **item,
                    "meta_policy_realized_effect": realized_effect,
                    "universe_refresh_priority": universe_refresh_priority,
                    "capital_intent": capital_intent,
                    "target_family_multiplier": round(target_family_multiplier, 6),
                    "capital_intent_reason_codes": [
                        f"policy_bridge_state:{policy_bridge_state}",
                        f"meta_policy_realized_effect:{realized_effect}",
                        f"universe_refresh_priority:{universe_refresh_priority}",
                    ],
                }
            )

        system_action = "hold_alpha_family_capital_intent"
        if constrain_count > 0:
            system_action = "constrain_fragile_alpha_family_capacity"
        elif expand_count > 0:
            system_action = "expand_supportive_alpha_family_capacity"

        return {
            "status": "ok",
            "items": items[:limit],
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-05",
                "policy_optimization_meta_control_learning": "PO-05",
                "system_level_learning_feedback_integration": "SLLFI-05",
            },
            "alpha_family_capital_intent_summary": {
                "family_count": min(len(items), limit),
                "expand_families": min(expand_count, len(items[:limit])),
                "constrain_families": min(constrain_count, len(items[:limit])),
                "hold_families": min(hold_count, len(items[:limit])),
                "system_alpha_family_capital_action": system_action,
            },
        }

    def alpha_portfolio_intake_queue_latest(self, limit: int = 20) -> dict[str, Any]:
        admission = self.alpha_admission_decision_latest(limit=max(limit * 3, 30))
        promotion_bridge = self.alpha_promotion_bridge_latest(limit=max(limit * 3, 30))
        capital_intent = self.alpha_family_capital_intent_latest(limit=max(limit * 2, 20))

        promotion_by_alpha = self._latest_by_key(list(promotion_bridge.get("items") or []), "alpha_id")
        capital_by_family = self._family_latest(list(capital_intent.get("items") or []))
        items: list[dict[str, Any]] = []
        queue_now_count = 0
        shadow_count = 0
        hold_count = 0
        reject_count = 0

        for item in list(admission.get("items") or []):
            alpha_id = str(item.get("alpha_id") or "")
            family = str(item.get("alpha_family") or "unknown")
            promotion_item = dict(promotion_by_alpha.get(alpha_id) or {})
            capital_item = dict(capital_by_family.get(family) or {})
            admission_decision = str(item.get("alpha_admission_decision") or "hold")
            promotion_bridge_status = str(promotion_item.get("promotion_bridge_status") or "hold")
            capital_family_intent = str(capital_item.get("capital_intent") or "hold")

            intake_status = "hold"
            intake_action = "hold_alpha_outside_portfolio"
            if admission_decision == "admit" and promotion_bridge_status == "accelerate" and capital_family_intent != "constrain":
                intake_status = "queue_now"
                intake_action = "queue_alpha_for_portfolio_intake"
                queue_now_count += 1
            elif admission_decision == "shadow":
                intake_status = "shadow"
                intake_action = "queue_alpha_for_shadow_intake"
                shadow_count += 1
            elif admission_decision == "reject":
                intake_status = "reject"
                intake_action = "reject_alpha_from_portfolio_intake"
                reject_count += 1
            else:
                hold_count += 1

            items.append(
                {
                    **item,
                    "promotion_bridge_status": promotion_bridge_status,
                    "promotion_bridge_action": promotion_item.get("promotion_bridge_action"),
                    "capital_intent": capital_family_intent,
                    "target_family_multiplier": capital_item.get("target_family_multiplier"),
                    "portfolio_intake_status": intake_status,
                    "portfolio_intake_action": intake_action,
                }
            )

        items.sort(
            key=lambda item: (
                {"queue_now": 0, "shadow": 1, "hold": 2, "reject": 3}.get(str(item.get("portfolio_intake_status")), 4),
                -float(item.get("rank_score", 0.0) or 0.0),
                str(item.get("alpha_id") or ""),
            )
        )
        items = items[:limit]

        system_action = "hold_alpha_portfolio_intake_queue"
        if queue_now_count > 0:
            system_action = "queue_expansion_alphas_for_portfolio_intake"
        elif shadow_count > 0:
            system_action = "maintain_shadow_alpha_portfolio_intake"

        return {
            "status": "ok",
            "items": items,
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-05",
                "research_promotion_intelligence": "RPI-06",
                "portfolio_intelligence": "PI-05",
            },
            "alpha_portfolio_intake_queue_summary": {
                "alpha_count": len(items),
                "queue_now_candidates": sum(1 for item in items if item.get("portfolio_intake_status") == "queue_now"),
                "shadow_candidates": sum(1 for item in items if item.get("portfolio_intake_status") == "shadow"),
                "hold_candidates": sum(1 for item in items if item.get("portfolio_intake_status") == "hold"),
                "reject_candidates": sum(1 for item in items if item.get("portfolio_intake_status") == "reject"),
                "system_alpha_portfolio_intake_action": system_action,
            },
        }

    def alpha_governed_universe_state_latest(self, limit: int = 20) -> dict[str, Any]:
        intake = self.alpha_portfolio_intake_queue_latest(limit=max(limit * 2, 20))
        transitions = self.research_promotion.persisted_governed_state_transitions_latest(limit=max(limit * 3, 30))
        transition_by_alpha = self._latest_by_key(list(transitions.get("items") or []), "alpha_id")

        items: list[dict[str, Any]] = []
        expand_count = 0
        shadow_count = 0
        prune_count = 0
        hold_count = 0

        for item in list(intake.get("items") or []):
            alpha_id = str(item.get("alpha_id") or "")
            transition = dict(transition_by_alpha.get(alpha_id) or {})
            intake_status = str(item.get("portfolio_intake_status") or "hold")
            governed_state = str(transition.get("new_governed_state") or item.get("current_lifecycle_state") or "candidate")

            governed_universe_state = "hold"
            if intake_status == "queue_now" and governed_state in {"promoted", "shadow", "candidate"}:
                governed_universe_state = "expand"
                expand_count += 1
            elif intake_status == "shadow" or governed_state == "shadow":
                governed_universe_state = "shadow"
                shadow_count += 1
            elif intake_status == "reject" or governed_state in {"retired", "rejected"}:
                governed_universe_state = "prune"
                prune_count += 1
            else:
                hold_count += 1

            items.append(
                {
                    **item,
                    "new_governed_state": governed_state,
                    "transition_id": transition.get("transition_id"),
                    "authority_surface": transition.get("authority_surface"),
                    "governed_universe_state": governed_universe_state,
                    "governed_universe_reason_codes": [
                        f"portfolio_intake_status:{intake_status}",
                        f"new_governed_state:{governed_state}",
                    ],
                }
            )

        system_action = "hold_alpha_governed_universe_state"
        if prune_count > 0:
            system_action = "prune_alpha_universe_under_governed_constraints"
        elif expand_count > 0:
            system_action = "expand_governed_alpha_universe"

        return {
            "status": "ok",
            "items": items[:limit],
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-05",
                "research_promotion_intelligence": "RPI-06",
            },
            "alpha_governed_universe_state_summary": {
                "alpha_count": min(len(items), limit),
                "expand_alphas": min(expand_count, len(items[:limit])),
                "shadow_alphas": min(shadow_count, len(items[:limit])),
                "prune_alphas": min(prune_count, len(items[:limit])),
                "hold_alphas": min(hold_count, len(items[:limit])),
                "system_alpha_governed_universe_action": system_action,
            },
        }

    def alpha_strategy_factory_readiness_latest(self, limit: int = 20) -> dict[str, Any]:
        promotion_bridge = self.alpha_promotion_bridge_latest(limit=max(limit * 2, 20))
        capital_intent = self.alpha_family_capital_intent_latest(limit=max(limit * 2, 20))
        intake = self.alpha_portfolio_intake_queue_latest(limit=max(limit * 2, 20))
        governed = self.alpha_governed_universe_state_latest(limit=max(limit * 2, 20))

        promotion_summary = promotion_bridge.get("alpha_promotion_bridge_summary") or {}
        capital_summary = capital_intent.get("alpha_family_capital_intent_summary") or {}
        intake_summary = intake.get("alpha_portfolio_intake_queue_summary") or {}
        governed_summary = governed.get("alpha_governed_universe_state_summary") or {}

        readiness_status = "ready"
        if int(governed_summary.get("prune_alphas", 0) or 0) > 0:
            readiness_status = "fragile"
        elif int(intake_summary.get("hold_candidates", 0) or 0) > int(intake_summary.get("queue_now_candidates", 0) or 0):
            readiness_status = "watch"

        return {
            "status": "ok",
            "alpha_strategy_factory_readiness": {
                "readiness_status": readiness_status,
                "accelerated_promotion_count": int(promotion_summary.get("accelerate_candidates", 0) or 0),
                "expand_family_count": int(capital_summary.get("expand_families", 0) or 0),
                "queue_now_intake_count": int(intake_summary.get("queue_now_candidates", 0) or 0),
                "expand_governed_alpha_count": int(governed_summary.get("expand_alphas", 0) or 0),
                "prune_governed_alpha_count": int(governed_summary.get("prune_alphas", 0) or 0),
                "system_alpha_strategy_factory_action": (
                    "stabilize_alpha_strategy_factory"
                    if readiness_status == "fragile"
                    else ("monitor_alpha_strategy_factory_backlog" if readiness_status == "watch" else "run_alpha_strategy_factory_forward")
                ),
            },
            "source_packets": {
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-05",
                "research_promotion_intelligence": "RPI-06",
                "portfolio_intelligence": "PI-05",
                "policy_optimization_meta_control_learning": "PO-05",
            },
        }
