from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.alpha_synthesis.aae_bridge import AlphaSynthesisAAEBridge
from ai_hedge_bot.alpha_synthesis.dsl.expression import AlphaExpression
from ai_hedge_bot.alpha_synthesis.dsl.nodes import AlphaNode
from ai_hedge_bot.alpha_synthesis.dsl.validator import validate_expression
from ai_hedge_bot.alpha_synthesis.evaluation.expression_evaluator import ExpressionEvaluator
from ai_hedge_bot.alpha_synthesis.generation_router import AlphaGenerationRouter
from ai_hedge_bot.alpha_synthesis.novelty.structural_novelty import score_structural_novelty
from ai_hedge_bot.alpha_synthesis.repositories.expression_repository import ExpressionRepository
from ai_hedge_bot.alpha_synthesis.repositories.synthesis_run_repository import SynthesisRunRepository
from ai_hedge_bot.alpha_synthesis.validation.semantic_prescreen import semantic_prescreen
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id, new_run_id
from ai_hedge_bot.services.strategy_evolution_regime_adaptation_intelligence_service import (
    StrategyEvolutionRegimeAdaptationIntelligenceService,
)


class AlphaSynthesisService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.router = AlphaGenerationRouter()
        self.evaluator = ExpressionEvaluator()
        self.expressions = ExpressionRepository()
        self.runs = SynthesisRunRepository()
        self.aae_bridge = AlphaSynthesisAAEBridge()
        self.strategy_evolution = StrategyEvolutionRegimeAdaptationIntelligenceService()

    def _expr_from_row(self, row: dict) -> AlphaExpression | None:
        payload = self.store.parse_json(row.get("ast_json"), {})
        if not payload:
            return None
        return AlphaExpression.from_root(AlphaNode.from_dict(payload))

    def _parent_rows(self, limit: int = 20) -> list[dict]:
        rows = self.expressions.list_recent_expressions(limit=max(limit * 3, 30))
        return [row for row in rows if str(row.get("status") or "") == "accepted"][:limit]

    def _expression_rows_by_id(self, limit: int = 200) -> dict[str, dict]:
        rows = self.expressions.list_recent_expressions(limit=limit)
        return {str(row.get("expression_id") or ""): row for row in rows}

    def _regime_payload(self, limit: int = 20) -> dict:
        return self.strategy_evolution.strategy_gating_decision_latest(limit=limit)

    @staticmethod
    def _brief_id(family: str, regime_bias: str, index: int) -> str:
        normalized_family = str(family or "unknown").replace(" ", "_")
        return f"hypothesis.{normalized_family}.{regime_bias}.{index + 1}"

    @staticmethod
    def _regime_bias(current_regime: str, family_regime_state: str, gating_decision: str) -> tuple[str, list[str], list[str]]:
        normalized_regime = str(current_regime or "balanced")
        normalized_family = str(family_regime_state or "balanced")
        normalized_gate = str(gating_decision or "shadow")

        if normalized_family == "risk_on" and normalized_gate == "allow":
            return (
                "expand",
                ["returns", "log_returns", "volume"],
                ["ts_rank", "ts_zscore", "rank"],
            )
        if normalized_family == "transition" or normalized_regime == "transition":
            return (
                "adapt",
                ["volatility", "high_low_range", "spread_bps"],
                ["ts_mean", "ts_std", "normalize"],
            )
        if normalized_family == "risk_off" or normalized_gate in {"gate", "retire"}:
            return (
                "constrain",
                ["volatility", "spread_bps", "orderflow_imbalance"],
                ["winsorize", "zscore", "cs_zscore"],
            )
        return (
            "observe",
            ["returns", "volume", "open_interest"],
            ["ts_mean", "rank", "normalize"],
        )

    @staticmethod
    def _expression_regime_fit_score(*, expression: dict, preferred_features: list[str], preferred_operators: list[str], regime_bias: str) -> tuple[float, str]:
        features = set(list(expression.get("feature_set") or []))
        operators = set(list(expression.get("operator_set") or []))
        preferred_feature_overlap = len(features & set(preferred_features))
        preferred_operator_overlap = len(operators & set(preferred_operators))
        base = 0.3 + (0.15 * preferred_feature_overlap) + (0.12 * preferred_operator_overlap)
        if regime_bias == "expand":
            base += 0.1
        elif regime_bias == "adapt":
            base += 0.06
        elif regime_bias == "constrain":
            base -= 0.04
        score = round(max(0.0, min(base, 0.95)), 6)
        if score >= 0.75:
            return score, "high_fit"
        if score >= 0.55:
            return score, "watch_fit"
        return score, "low_fit"

    def _hypothesis_briefs(self, limit: int = 20) -> dict:
        agenda = self.alpha_regime_synthesis_agenda_latest(limit=max(limit, 4))
        expression_map = self.alpha_regime_expression_map_latest(limit=max(limit, 4))
        family_map = {
            str(item.get("alpha_family") or ""): item
            for item in list(expression_map.get("items") or [])
        }
        items: list[dict] = []
        for idx, agenda_item in enumerate(list(agenda.get("items") or [])[:limit]):
            family = str(agenda_item.get("alpha_family") or "unknown")
            family_state = family_map.get(family, {})
            regime_bias = str(agenda_item.get("regime_bias") or "observe")
            hypothesis_brief = {
                "brief_id": self._brief_id(family, regime_bias, idx),
                "alpha_family": family,
                "current_regime": agenda.get("current_regime"),
                "regime_bias": regime_bias,
                "preferred_features": list(agenda_item.get("preferred_features") or []),
                "preferred_operators": list(agenda_item.get("preferred_operators") or []),
                "aligned_expressions": int(family_state.get("aligned_expressions", 0) or 0),
                "watch_expressions": int(family_state.get("watch_expressions", 0) or 0),
                "misaligned_expressions": int(family_state.get("misaligned_expressions", 0) or 0),
                "hypothesis_text": (
                    f"Generate a symbolic alpha for family {family} under regime {agenda.get('current_regime')} "
                    f"with bias {regime_bias}, emphasizing features {', '.join(list(agenda_item.get('preferred_features') or []))} "
                    f"and operators {', '.join(list(agenda_item.get('preferred_operators') or []))}."
                ),
            }
            items.append(hypothesis_brief)
        return {
            "status": "ok",
            "current_regime": agenda.get("current_regime"),
            "regime_confidence": agenda.get("regime_confidence"),
            "items": items,
            "as_of": agenda.get("as_of"),
        }

    @staticmethod
    def _hypothesis_prompt(brief: dict) -> dict:
        return {
            "brief_id": brief.get("brief_id"),
            "prompt_mode": "deterministic_llm_assist",
            "system_prompt": "Translate the hypothesis brief into one valid symbolic alpha expression using the approved DSL only.",
            "user_prompt": brief.get("hypothesis_text"),
            "translation_constraints": {
                "preferred_features": list(brief.get("preferred_features") or []),
                "preferred_operators": list(brief.get("preferred_operators") or []),
                "alpha_family": brief.get("alpha_family"),
                "regime_bias": brief.get("regime_bias"),
            },
        }

    def _execute_run(self, *, generator_type: str, requested_count: int, parents: list[dict] | None = None, config: dict | None = None) -> dict:
        config = config or {}
        latest = self.runs.latest_run(generator_type=generator_type)
        recent_candidates = self.runs.list_recent_candidates(limit=5, generator_type=generator_type)
        if latest and recent_candidates:
            return latest

        started_at = utc_now_iso()
        run_id = new_run_id()
        library_rows = self.expressions.list_recent_expressions(limit=200)
        parent_exprs = [self._expr_from_row(row) for row in list(parents or [])]
        parent_exprs = [expr for expr in parent_exprs if expr is not None]
        generated = 0
        accepted = 0
        rejected = 0
        if generator_type == "mutation":
            generated_exprs = self.router.generate("mutation", parents=parent_exprs, n=requested_count, config=config)
        elif generator_type == "crossover":
            generated_exprs = self.router.generate("crossover", parents=parent_exprs, n=requested_count, config=config)
        elif generator_type == "hypothesis":
            generated_exprs = self.router.generate("hypothesis", parents=[], n=requested_count, config=config)
        else:
            generated_exprs = self.router.generate("random", parents=[], n=requested_count, config={"max_depth": 4, **config})

        for index, expr in enumerate(generated_exprs):
            generated += 1
            expression_id = new_cycle_id()
            valid, validation_reasons = validate_expression(expr)
            novelty = score_structural_novelty(expr, library_rows)
            metrics = self.evaluator.evaluate(expr)
            prescreen_status, prescreen_reasons = semantic_prescreen(metrics)

            rejection_reason = None
            validation_status = "accepted"
            status = "accepted"
            if not valid:
                validation_status = "dsl_rejected"
                rejection_reason = "|".join(validation_reasons)
                status = "rejected"
            elif novelty.get("novelty_verdict") == "duplicate":
                validation_status = "duplicate"
                rejection_reason = "duplicate_expression_hash"
                status = "rejected"
            elif prescreen_status != "accepted":
                validation_status = "semantic_rejected"
                rejection_reason = "|".join(prescreen_reasons)
                status = "rejected"

            self.expressions.insert_expression(
                expression_id,
                expr,
                {
                    "generator_type": generator_type,
                    "parent_expression_ids": [row.get("expression_id") for row in list(parents or [])[:2]],
                    "status": status,
                },
            )
            aae_result = {"aae_submission_status": "not_submitted", "alpha_id": None}
            if status == "accepted":
                aae_result = self.aae_bridge.submit(expression_id, expr)
                accepted += 1
            else:
                rejected += 1
            candidate_id = new_cycle_id()
            self.store.append(
                "alpha_synthesis_candidates",
                {
                    "candidate_id": candidate_id,
                    "run_id": run_id,
                    "expression_id": expression_id,
                    "formula": expr.formula,
                    "generator_type": generator_type,
                    "novelty_score": float(novelty.get("novelty_score", 0.0) or 0.0),
                    "novelty_verdict": novelty.get("novelty_verdict"),
                    "validation_status": validation_status,
                    "rejection_reason": rejection_reason,
                    "aae_submission_status": aae_result.get("aae_submission_status"),
                    "alpha_id": aae_result.get("alpha_id"),
                    "created_at": utc_now_iso(),
                },
            )
            self.store.append(
                "alpha_synthesis_novelty",
                {
                    "novelty_id": new_cycle_id(),
                    "candidate_id": candidate_id,
                    "expression_id": expression_id,
                    "nearest_expression_id": novelty.get("nearest_expression_id"),
                    "exact_duplicate": bool(novelty.get("exact_duplicate")),
                    "operator_jaccard_distance": float(novelty.get("operator_jaccard_distance", 0.0) or 0.0),
                    "feature_jaccard_distance": float(novelty.get("feature_jaccard_distance", 0.0) or 0.0),
                    "token_distance": float(novelty.get("token_distance", 0.0) or 0.0),
                    "novelty_score": float(novelty.get("novelty_score", 0.0) or 0.0),
                    "novelty_verdict": novelty.get("novelty_verdict"),
                    "created_at": utc_now_iso(),
                },
            )
            library_rows.insert(
                0,
                {
                    "expression_id": expression_id,
                    "expression_hash": expr.expression_hash,
                    "formula": expr.formula,
                    "feature_set": expr.feature_set,
                    "operator_set": expr.operator_set,
                },
            )

        completed_at = utc_now_iso()
        self.runs.insert_run(
            {
                "run_id": run_id,
                "generator_type": generator_type,
                "config_json": self.store.to_json({"requested_count": requested_count, **config}),
                "requested_count": requested_count,
                "generated_count": generated,
                "accepted_count": accepted,
                "rejected_count": rejected,
                "started_at": started_at,
                "completed_at": completed_at,
                "status": "ok",
            }
        )
        return self.runs.latest_run(generator_type=generator_type)

    def _ensure_recent_run(self, requested_count: int = 6) -> dict:
        return self._execute_run(generator_type="random", requested_count=requested_count, config={"max_depth": 4})

    def alpha_synthesis_candidates_latest(self, limit: int = 20) -> dict:
        run = self._ensure_recent_run()
        rows = self.runs.list_recent_candidates(limit=max(limit, 1))
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "generator_type": run.get("generator_type"),
            "items": rows[:limit],
            "alpha_synthesis_candidates_summary": {
                "candidate_count": min(len(rows), limit),
                "accepted_candidates": sum(1 for row in rows[:limit] if row.get("validation_status") == "accepted"),
                "rejected_candidates": sum(1 for row in rows[:limit] if row.get("validation_status") != "accepted"),
                "system_alpha_synthesis_action": "continue_symbolic_structure_search",
            },
            "as_of": run.get("completed_at"),
        }

    def alpha_structure_search_state_latest(self, limit: int = 20) -> dict:
        run = self._ensure_recent_run()
        candidates = self.runs.list_recent_candidates(limit=max(limit * 3, 20))
        verdicts: dict[str, int] = {}
        for row in candidates:
            verdict = str(row.get("novelty_verdict") or "unknown")
            verdicts[verdict] = verdicts.get(verdict, 0) + 1
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "generator_type": run.get("generator_type"),
            "search_budget": {
                "requested_count": int(run.get("requested_count", 0) or 0),
                "generated_count": int(run.get("generated_count", 0) or 0),
                "accepted_count": int(run.get("accepted_count", 0) or 0),
                "rejected_count": int(run.get("rejected_count", 0) or 0),
            },
            "search_state": {
                "active_generator_type": run.get("generator_type"),
                "feature_space": "dsl_feature_catalog_v1",
                "operator_space": "dsl_operator_catalog_v1",
                "failure_reason_distribution": verdicts,
                "status": run.get("status"),
            },
            "as_of": run.get("completed_at"),
        }

    def alpha_novelty_evaluation_latest(self, limit: int = 20) -> dict:
        run = self._ensure_recent_run()
        rows = self.runs.list_recent_novelty(limit=max(limit, 1))
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "items": rows[:limit],
            "alpha_novelty_evaluation_summary": {
                "evaluated_count": min(len(rows), limit),
                "novel_count": sum(1 for row in rows[:limit] if row.get("novelty_verdict") == "novel"),
                "near_duplicate_count": sum(1 for row in rows[:limit] if row.get("novelty_verdict") == "near_duplicate"),
                "duplicate_count": sum(1 for row in rows[:limit] if row.get("novelty_verdict") == "duplicate"),
                "system_alpha_novelty_action": "score_new_symbolic_structures_against_library",
            },
            "as_of": run.get("completed_at"),
        }

    def alpha_expression_library_latest(self, limit: int = 20) -> dict:
        run = self._ensure_recent_run()
        rows = self.expressions.list_recent_expressions(limit=max(limit, 1))
        items = [
            {
                "expression_id": row.get("expression_id"),
                "expression_hash": row.get("expression_hash"),
                "formula": row.get("formula"),
                "depth": row.get("depth"),
                "node_count": row.get("node_count"),
                "feature_set": row.get("feature_set") or [],
                "operator_set": row.get("operator_set") or [],
                "generator_type": row.get("generator_type"),
                "status": row.get("status"),
                "created_at": row.get("created_at"),
            }
            for row in rows[:limit]
        ]
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "items": items,
            "alpha_expression_library_summary": {
                "expression_count": len(items),
                "accepted_expressions": sum(1 for item in items if item.get("status") == "accepted"),
                "rejected_expressions": sum(1 for item in items if item.get("status") == "rejected"),
                "system_alpha_expression_library_action": "preserve_recent_symbolic_expression_lineage",
            },
            "as_of": run.get("completed_at"),
        }

    def alpha_synthesis_effectiveness_latest(self, limit: int = 20) -> dict:
        candidates = self.alpha_synthesis_candidates_latest(limit=max(limit * 2, 20))
        novelty = self.alpha_novelty_evaluation_latest(limit=max(limit * 2, 20))
        library = self.alpha_expression_library_latest(limit=max(limit * 2, 20))

        candidate_summary = candidates.get("alpha_synthesis_candidates_summary") or {}
        novelty_summary = novelty.get("alpha_novelty_evaluation_summary") or {}
        library_summary = library.get("alpha_expression_library_summary") or {}

        effectiveness_status = "effective"
        if int(candidate_summary.get("accepted_candidates", 0) or 0) == 0:
            effectiveness_status = "insufficient"
        elif int(novelty_summary.get("duplicate_count", 0) or 0) > int(novelty_summary.get("novel_count", 0) or 0):
            effectiveness_status = "watch"

        return {
            "status": "ok",
            "alpha_synthesis_effectiveness": {
                "effectiveness_status": effectiveness_status,
                "accepted_candidate_count": int(candidate_summary.get("accepted_candidates", 0) or 0),
                "novel_candidate_count": int(novelty_summary.get("novel_count", 0) or 0),
                "expression_library_count": int(library_summary.get("expression_count", 0) or 0),
                "system_alpha_synthesis_effectiveness_action": (
                    "improve_symbolic_generator_core"
                    if effectiveness_status == "insufficient"
                    else ("monitor_symbolic_search_duplication" if effectiveness_status == "watch" else "continue_symbolic_alpha_generation")
                ),
            },
            "source_packets": {
                "alpha_synthesis_structural_discovery_intelligence": "ASD-01",
                "autonomous_alpha_expansion_strategy_generation_intelligence": "AAE-05",
            },
        }

    def alpha_parent_candidates_latest(self, limit: int = 20) -> dict:
        self._ensure_recent_run()
        rows = self._parent_rows(limit=limit)
        items = [
            {
                "expression_id": row.get("expression_id"),
                "formula": row.get("formula"),
                "generator_type": row.get("generator_type"),
                "feature_set": row.get("feature_set") or [],
                "operator_set": row.get("operator_set") or [],
                "parent_candidate_status": "eligible_parent",
            }
            for row in rows[:limit]
        ]
        return {
            "status": "ok",
            "items": items,
            "alpha_parent_candidates_summary": {
                "candidate_count": len(items),
                "eligible_parents": len(items),
                "system_alpha_parent_action": "select_recent_accepted_expressions_as_parents",
            },
        }

    def alpha_mutation_candidates_latest(self, limit: int = 20) -> dict:
        parents = self._parent_rows(limit=max(limit, 4))
        run = self._execute_run(generator_type="mutation", requested_count=max(limit, 4), parents=parents, config={"mode": "mutation"})
        rows = self.runs.list_recent_candidates(limit=max(limit, 1), generator_type="mutation")
        expressions_by_id = self._expression_rows_by_id(limit=max(limit * 5, 50))
        items = []
        for idx, row in enumerate(rows[:limit]):
            parent_row = parents[idx % len(parents)] if parents else {}
            expr_row = dict(expressions_by_id.get(str(row.get("expression_id") or "")) or {})
            items.append(
                {
                    **row,
                    "parent_expression_id": parent_row.get("expression_id"),
                    "feature_set": expr_row.get("feature_set") or [],
                    "operator_set": expr_row.get("operator_set") or [],
                    "mutation_candidate_status": "accepted_mutation" if row.get("validation_status") == "accepted" else "rejected_mutation",
                }
            )
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "items": items,
            "alpha_mutation_candidates_summary": {
                "candidate_count": len(items),
                "accepted_mutations": sum(1 for item in items if item.get("validation_status") == "accepted"),
                "rejected_mutations": sum(1 for item in items if item.get("validation_status") != "accepted"),
                "system_alpha_mutation_action": "continue_mutation_search",
            },
            "as_of": run.get("completed_at"),
        }

    def alpha_crossover_candidates_latest(self, limit: int = 20) -> dict:
        parents = self._parent_rows(limit=max(limit, 6))
        run = self._execute_run(generator_type="crossover", requested_count=max(limit, 4), parents=parents, config={"mode": "crossover"})
        rows = self.runs.list_recent_candidates(limit=max(limit, 1), generator_type="crossover")
        expressions_by_id = self._expression_rows_by_id(limit=max(limit * 5, 50))
        items = []
        for idx, row in enumerate(rows[:limit]):
            left = parents[idx % len(parents)] if parents else {}
            right = parents[(idx + 1) % len(parents)] if len(parents) > 1 else {}
            expr_row = dict(expressions_by_id.get(str(row.get("expression_id") or "")) or {})
            items.append(
                {
                    **row,
                    "left_parent_expression_id": left.get("expression_id"),
                    "right_parent_expression_id": right.get("expression_id"),
                    "feature_set": expr_row.get("feature_set") or [],
                    "operator_set": expr_row.get("operator_set") or [],
                    "crossover_candidate_status": "accepted_crossover" if row.get("validation_status") == "accepted" else "rejected_crossover",
                }
            )
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "items": items,
            "alpha_crossover_candidates_summary": {
                "candidate_count": len(items),
                "accepted_crossovers": sum(1 for item in items if item.get("validation_status") == "accepted"),
                "rejected_crossovers": sum(1 for item in items if item.get("validation_status") != "accepted"),
                "system_alpha_crossover_action": "continue_crossover_search",
            },
            "as_of": run.get("completed_at"),
        }

    def alpha_evolution_search_state_latest(self, limit: int = 20) -> dict:
        mutation = self.alpha_mutation_candidates_latest(limit=max(limit, 4))
        crossover = self.alpha_crossover_candidates_latest(limit=max(limit, 4))
        parent = self.alpha_parent_candidates_latest(limit=max(limit, 4))
        mutation_summary = mutation.get("alpha_mutation_candidates_summary") or {}
        crossover_summary = crossover.get("alpha_crossover_candidates_summary") or {}
        parent_summary = parent.get("alpha_parent_candidates_summary") or {}
        return {
            "status": "ok",
            "search_state": {
                "active_modes": ["mutation", "crossover"],
                "eligible_parent_count": int(parent_summary.get("eligible_parents", 0) or 0),
                "accepted_mutation_count": int(mutation_summary.get("accepted_mutations", 0) or 0),
                "accepted_crossover_count": int(crossover_summary.get("accepted_crossovers", 0) or 0),
                "router_state": "evolutionary_search_active",
            },
            "alpha_evolution_search_state_summary": {
                "system_alpha_evolution_action": "continue_evolutionary_symbolic_search",
            },
        }

    def alpha_evolution_effectiveness_latest(self, limit: int = 20) -> dict:
        mutation = self.alpha_mutation_candidates_latest(limit=max(limit, 4))
        crossover = self.alpha_crossover_candidates_latest(limit=max(limit, 4))
        state = self.alpha_evolution_search_state_latest(limit=max(limit, 4))
        mutation_summary = mutation.get("alpha_mutation_candidates_summary") or {}
        crossover_summary = crossover.get("alpha_crossover_candidates_summary") or {}
        accepted_mutations = int(mutation_summary.get("accepted_mutations", 0) or 0)
        accepted_crossovers = int(crossover_summary.get("accepted_crossovers", 0) or 0)
        effectiveness_status = "effective"
        if accepted_mutations + accepted_crossovers == 0:
            effectiveness_status = "insufficient"
        elif accepted_crossovers == 0 or accepted_mutations == 0:
            effectiveness_status = "watch"
        return {
            "status": "ok",
            "alpha_evolution_effectiveness": {
                "effectiveness_status": effectiveness_status,
                "accepted_mutation_count": accepted_mutations,
                "accepted_crossover_count": accepted_crossovers,
                "system_alpha_evolution_effectiveness_action": (
                    "improve_evolutionary_search_generators"
                    if effectiveness_status == "insufficient"
                    else ("rebalance_mutation_and_crossover_mix" if effectiveness_status == "watch" else "continue_evolutionary_search")
                ),
            },
            "source_packets": {
                "alpha_synthesis_structural_discovery_intelligence": "ASD-02",
                "alpha_synthesis_structural_discovery_intelligence_base": "ASD-01",
            },
            "search_state": state.get("search_state") or {},
        }

    def alpha_regime_synthesis_agenda_latest(self, limit: int = 20) -> dict:
        regime = self._regime_payload(limit=max(limit, 4))
        items: list[dict] = []
        expand_count = 0
        adapt_count = 0
        constrain_count = 0
        observe_count = 0

        for item in list(regime.get("items") or [])[:limit]:
            regime_bias, preferred_features, preferred_operators = self._regime_bias(
                str(regime.get("current_regime") or "balanced"),
                str(item.get("family_regime_state") or "balanced"),
                str(item.get("strategy_gating_decision") or "shadow"),
            )
            if regime_bias == "expand":
                expand_count += 1
            elif regime_bias == "adapt":
                adapt_count += 1
            elif regime_bias == "constrain":
                constrain_count += 1
            else:
                observe_count += 1
            items.append(
                {
                    "alpha_family": item.get("alpha_family"),
                    "current_regime": regime.get("current_regime"),
                    "family_regime_state": item.get("family_regime_state"),
                    "strategy_gating_decision": item.get("strategy_gating_decision"),
                    "regime_bias": regime_bias,
                    "preferred_features": preferred_features,
                    "preferred_operators": preferred_operators,
                    "regime_synthesis_action": (
                        "expand_symbolic_search"
                        if regime_bias == "expand"
                        else ("adapt_symbolic_search" if regime_bias == "adapt" else ("constrain_symbolic_search" if regime_bias == "constrain" else "observe_symbolic_search"))
                    ),
                }
            )

        system_action = "observe_regime_conditioned_synthesis"
        if constrain_count > 0:
            system_action = "constrain_regime_fragile_symbolic_search"
        elif expand_count > 0:
            system_action = "expand_regime_supportive_symbolic_search"
        elif adapt_count > 0:
            system_action = "adapt_symbolic_search_to_regime_shift"

        return {
            "status": "ok",
            "current_regime": regime.get("current_regime"),
            "regime_confidence": regime.get("regime_confidence"),
            "items": items,
            "alpha_regime_synthesis_agenda_summary": {
                "family_count": len(items),
                "expand_families": expand_count,
                "adapt_families": adapt_count,
                "constrain_families": constrain_count,
                "observe_families": observe_count,
                "system_alpha_regime_synthesis_action": system_action,
            },
            "as_of": regime.get("as_of"),
        }

    def alpha_regime_targeted_candidates_latest(self, limit: int = 20) -> dict:
        agenda = self.alpha_regime_synthesis_agenda_latest(limit=max(limit, 4))
        evolution_candidates = list(self.alpha_mutation_candidates_latest(limit=max(limit, 4)).get("items") or []) + list(
            self.alpha_crossover_candidates_latest(limit=max(limit, 4)).get("items") or []
        )
        if not evolution_candidates:
            evolution_candidates = list(self.alpha_synthesis_candidates_latest(limit=max(limit, 4)).get("items") or [])

        items: list[dict] = []
        high_count = 0
        watch_count = 0
        low_count = 0
        agenda_items = list(agenda.get("items") or [])
        for idx, candidate in enumerate(evolution_candidates[:limit]):
            agenda_item = agenda_items[idx % len(agenda_items)] if agenda_items else {}
            fit_score, fit_class = self._expression_regime_fit_score(
                expression={
                    "feature_set": candidate.get("feature_set") or [],
                    "operator_set": candidate.get("operator_set") or [],
                },
                preferred_features=list(agenda_item.get("preferred_features") or []),
                preferred_operators=list(agenda_item.get("preferred_operators") or []),
                regime_bias=str(agenda_item.get("regime_bias") or "observe"),
            )
            if fit_class == "high_fit":
                high_count += 1
            elif fit_class == "watch_fit":
                watch_count += 1
            else:
                low_count += 1
            items.append(
                {
                    **candidate,
                    "target_alpha_family": agenda_item.get("alpha_family"),
                    "target_regime_bias": agenda_item.get("regime_bias"),
                    "current_regime": agenda.get("current_regime"),
                    "regime_fit_score": fit_score,
                    "regime_fit_class": fit_class,
                    "regime_target_action": (
                        "prioritize_regime_targeted_validation"
                        if fit_class == "high_fit"
                        else ("keep_under_regime_watch" if fit_class == "watch_fit" else "deprioritize_regime_misaligned_candidate")
                    ),
                }
            )

        return {
            "status": "ok",
            "current_regime": agenda.get("current_regime"),
            "regime_confidence": agenda.get("regime_confidence"),
            "items": items,
            "alpha_regime_targeted_candidates_summary": {
                "candidate_count": len(items),
                "high_fit_candidates": high_count,
                "watch_fit_candidates": watch_count,
                "low_fit_candidates": low_count,
                "system_alpha_regime_targeted_action": "prioritize_high_fit_regime_candidates" if high_count > 0 else "continue_regime_targeted_search",
            },
            "as_of": agenda.get("as_of"),
        }

    def alpha_regime_fit_evaluation_latest(self, limit: int = 20) -> dict:
        targeted = self.alpha_regime_targeted_candidates_latest(limit=max(limit, 4))
        items = []
        aligned_count = 0
        watch_count = 0
        misaligned_count = 0
        for item in list(targeted.get("items") or [])[:limit]:
            fit_class = str(item.get("regime_fit_class") or "low_fit")
            evaluation = "misaligned"
            if fit_class == "high_fit":
                evaluation = "aligned"
                aligned_count += 1
            elif fit_class == "watch_fit":
                evaluation = "watch"
                watch_count += 1
            else:
                misaligned_count += 1
            items.append(
                {
                    **item,
                    "regime_fit_evaluation": evaluation,
                    "regime_fit_reason_codes": [
                        f"target_regime_bias:{item.get('target_regime_bias')}",
                        f"regime_fit_score:{item.get('regime_fit_score')}",
                        f"regime_fit_class:{fit_class}",
                    ],
                }
            )
        return {
            "status": "ok",
            "current_regime": targeted.get("current_regime"),
            "items": items,
            "alpha_regime_fit_evaluation_summary": {
                "candidate_count": len(items),
                "aligned_candidates": aligned_count,
                "watch_candidates": watch_count,
                "misaligned_candidates": misaligned_count,
                "system_alpha_regime_fit_action": "promote_aligned_regime_candidates" if aligned_count > 0 else "continue_regime_fit_screening",
            },
            "as_of": targeted.get("as_of"),
        }

    def alpha_regime_expression_map_latest(self, limit: int = 20) -> dict:
        fit = self.alpha_regime_fit_evaluation_latest(limit=max(limit, 4))
        grouped: dict[str, dict] = {}
        for item in list(fit.get("items") or []):
            family = str(item.get("target_alpha_family") or "unknown")
            row = grouped.setdefault(
                family,
                {
                    "alpha_family": family,
                    "current_regime": fit.get("current_regime"),
                    "aligned_expressions": 0,
                    "watch_expressions": 0,
                    "misaligned_expressions": 0,
                    "expression_ids": [],
                },
            )
            evaluation = str(item.get("regime_fit_evaluation") or "misaligned")
            if evaluation == "aligned":
                row["aligned_expressions"] += 1
            elif evaluation == "watch":
                row["watch_expressions"] += 1
            else:
                row["misaligned_expressions"] += 1
            row["expression_ids"].append(item.get("expression_id"))
        items = list(grouped.values())[:limit]
        return {
            "status": "ok",
            "current_regime": fit.get("current_regime"),
            "items": items,
            "alpha_regime_expression_map_summary": {
                "family_count": len(items),
                "families_with_aligned_expressions": sum(1 for item in items if int(item.get("aligned_expressions", 0) or 0) > 0),
                "system_alpha_regime_map_action": "maintain_family_expression_regime_map",
            },
            "as_of": fit.get("as_of"),
        }

    def alpha_regime_synthesis_effectiveness_latest(self, limit: int = 20) -> dict:
        agenda = self.alpha_regime_synthesis_agenda_latest(limit=max(limit, 4))
        targeted = self.alpha_regime_targeted_candidates_latest(limit=max(limit, 4))
        fit = self.alpha_regime_fit_evaluation_latest(limit=max(limit, 4))
        expression_map = self.alpha_regime_expression_map_latest(limit=max(limit, 4))
        target_summary = targeted.get("alpha_regime_targeted_candidates_summary") or {}
        fit_summary = fit.get("alpha_regime_fit_evaluation_summary") or {}
        map_summary = expression_map.get("alpha_regime_expression_map_summary") or {}
        effectiveness_status = "effective"
        if int(fit_summary.get("aligned_candidates", 0) or 0) == 0:
            effectiveness_status = "insufficient"
        elif int(target_summary.get("watch_fit_candidates", 0) or 0) > int(target_summary.get("high_fit_candidates", 0) or 0):
            effectiveness_status = "watch"
        return {
            "status": "ok",
            "current_regime": agenda.get("current_regime"),
            "alpha_regime_synthesis_effectiveness": {
                "effectiveness_status": effectiveness_status,
                "aligned_candidate_count": int(fit_summary.get("aligned_candidates", 0) or 0),
                "watch_candidate_count": int(fit_summary.get("watch_candidates", 0) or 0),
                "mapped_family_count": int(map_summary.get("family_count", 0) or 0),
                "system_alpha_regime_synthesis_effectiveness_action": (
                    "improve_regime_conditioned_search_bias"
                    if effectiveness_status == "insufficient"
                    else ("monitor_regime_conditioned_candidate_mix" if effectiveness_status == "watch" else "continue_regime_conditioned_symbolic_search")
                ),
            },
            "source_packets": {
                "alpha_synthesis_structural_discovery_intelligence": "ASD-03",
                "strategy_evolution_regime_adaptation_intelligence": "SERI-05",
            },
            "as_of": agenda.get("as_of"),
        }

    def alpha_hypothesis_agenda_latest(self, limit: int = 20) -> dict:
        briefs = self._hypothesis_briefs(limit=max(limit, 4))
        items = list(briefs.get("items") or [])[:limit]
        return {
            "status": "ok",
            "current_regime": briefs.get("current_regime"),
            "regime_confidence": briefs.get("regime_confidence"),
            "items": items,
            "alpha_hypothesis_agenda_summary": {
                "brief_count": len(items),
                "families_with_regime_bias": sum(1 for item in items if str(item.get("regime_bias") or "") != "observe"),
                "system_alpha_hypothesis_action": "prepare_regime_conditioned_hypothesis_briefs",
            },
            "as_of": briefs.get("as_of"),
        }

    def alpha_llm_hypothesis_prompts_latest(self, limit: int = 20) -> dict:
        agenda = self._hypothesis_briefs(limit=max(limit, 4))
        items = [self._hypothesis_prompt(brief) for brief in list(agenda.get("items") or [])[:limit]]
        return {
            "status": "ok",
            "current_regime": agenda.get("current_regime"),
            "items": items,
            "alpha_llm_hypothesis_prompts_summary": {
                "prompt_count": len(items),
                "constrained_prompts": len(items),
                "system_alpha_llm_prompt_action": "translate_hypothesis_briefs_into_prompt_packs",
            },
            "as_of": agenda.get("as_of"),
        }

    def alpha_llm_translation_candidates_latest(self, limit: int = 20) -> dict:
        agenda = self._hypothesis_briefs(limit=max(limit, 4))
        briefs = list(agenda.get("items") or [])
        run = self._execute_run(
            generator_type="hypothesis",
            requested_count=max(limit, max(len(briefs), 1)),
            config={"briefs": briefs},
        )
        rows = self.runs.list_recent_candidates(limit=max(limit, 1), generator_type="hypothesis")
        expressions_by_id = self._expression_rows_by_id(limit=max(limit * 5, 50))
        items = []
        for idx, row in enumerate(rows[:limit]):
            brief = briefs[idx % len(briefs)] if briefs else {}
            expr_row = dict(expressions_by_id.get(str(row.get("expression_id") or "")) or {})
            items.append(
                {
                    **row,
                    "brief_id": brief.get("brief_id"),
                    "alpha_family": brief.get("alpha_family"),
                    "regime_bias": brief.get("regime_bias"),
                    "hypothesis_text": brief.get("hypothesis_text"),
                    "preferred_features": list(brief.get("preferred_features") or []),
                    "preferred_operators": list(brief.get("preferred_operators") or []),
                    "feature_set": expr_row.get("feature_set") or [],
                    "operator_set": expr_row.get("operator_set") or [],
                    "translation_candidate_status": "accepted_translation" if row.get("validation_status") == "accepted" else "rejected_translation",
                }
            )
        return {
            "status": "ok",
            "current_regime": agenda.get("current_regime"),
            "run_id": run.get("run_id"),
            "items": items,
            "alpha_llm_translation_candidates_summary": {
                "candidate_count": len(items),
                "accepted_translations": sum(1 for item in items if item.get("validation_status") == "accepted"),
                "rejected_translations": sum(1 for item in items if item.get("validation_status") != "accepted"),
                "system_alpha_llm_translation_action": "translate_hypothesis_briefs_into_symbolic_candidates",
            },
            "as_of": run.get("completed_at"),
        }

    def alpha_hypothesis_critique_latest(self, limit: int = 20) -> dict:
        translations = self.alpha_llm_translation_candidates_latest(limit=max(limit, 4))
        items = []
        strong_count = 0
        watch_count = 0
        weak_count = 0
        for item in list(translations.get("items") or [])[:limit]:
            fit_score, fit_class = self._expression_regime_fit_score(
                expression={
                    "feature_set": item.get("feature_set") or [],
                    "operator_set": item.get("operator_set") or [],
                },
                preferred_features=list(item.get("preferred_features") or []),
                preferred_operators=list(item.get("preferred_operators") or []),
                regime_bias=str(item.get("regime_bias") or "observe"),
            )
            novelty_score = float(item.get("novelty_score", 0.0) or 0.0)
            critique_score = round(min(0.98, 0.45 + (0.35 * fit_score) + (0.25 * novelty_score)), 6)
            critique_status = "weak"
            if critique_score >= 0.72 and str(item.get("validation_status") or "") == "accepted":
                critique_status = "strong"
                strong_count += 1
            elif critique_score >= 0.58:
                critique_status = "watch"
                watch_count += 1
            else:
                weak_count += 1
            items.append(
                {
                    **item,
                    "hypothesis_fit_score": fit_score,
                    "hypothesis_fit_class": fit_class,
                    "hypothesis_critique_score": critique_score,
                    "hypothesis_critique_status": critique_status,
                    "hypothesis_critique_action": (
                        "promote_hypothesis_candidate"
                        if critique_status == "strong"
                        else ("revise_hypothesis_prompt" if critique_status == "watch" else "discard_hypothesis_translation")
                    ),
                }
            )
        return {
            "status": "ok",
            "current_regime": translations.get("current_regime"),
            "items": items,
            "alpha_hypothesis_critique_summary": {
                "candidate_count": len(items),
                "strong_candidates": strong_count,
                "watch_candidates": watch_count,
                "weak_candidates": weak_count,
                "system_alpha_hypothesis_critique_action": "retain_only_strong_hypothesis_translations" if strong_count > 0 else "tighten_hypothesis_generation_prompts",
            },
            "as_of": translations.get("as_of"),
        }

    def alpha_hypothesis_effectiveness_latest(self, limit: int = 20) -> dict:
        prompts = self.alpha_llm_hypothesis_prompts_latest(limit=max(limit, 4))
        translations = self.alpha_llm_translation_candidates_latest(limit=max(limit, 4))
        critique = self.alpha_hypothesis_critique_latest(limit=max(limit, 4))
        prompt_summary = prompts.get("alpha_llm_hypothesis_prompts_summary") or {}
        translation_summary = translations.get("alpha_llm_translation_candidates_summary") or {}
        critique_summary = critique.get("alpha_hypothesis_critique_summary") or {}
        effectiveness_status = "effective"
        if int(critique_summary.get("strong_candidates", 0) or 0) == 0:
            effectiveness_status = "insufficient"
        elif int(translation_summary.get("rejected_translations", 0) or 0) >= int(translation_summary.get("accepted_translations", 0) or 0):
            effectiveness_status = "watch"
        return {
            "status": "ok",
            "current_regime": prompts.get("current_regime"),
            "alpha_hypothesis_effectiveness": {
                "effectiveness_status": effectiveness_status,
                "prompt_count": int(prompt_summary.get("prompt_count", 0) or 0),
                "accepted_translation_count": int(translation_summary.get("accepted_translations", 0) or 0),
                "strong_candidate_count": int(critique_summary.get("strong_candidates", 0) or 0),
                "system_alpha_hypothesis_effectiveness_action": (
                    "improve_hypothesis_translation_constraints"
                    if effectiveness_status == "insufficient"
                    else ("monitor_hypothesis_translation_quality" if effectiveness_status == "watch" else "continue_llm_assisted_hypothesis_generation")
                ),
            },
            "source_packets": {
                "alpha_synthesis_structural_discovery_intelligence": "ASD-04",
                "alpha_synthesis_structural_discovery_intelligence_regime": "ASD-03",
            },
            "as_of": prompts.get("as_of"),
        }

    def alpha_hypothesis_feedback_queue_latest(self, limit: int = 20) -> dict:
        critique = self.alpha_hypothesis_critique_latest(limit=max(limit, 4))
        items = []
        revise_count = 0
        retain_count = 0
        drop_count = 0
        for item in list(critique.get("items") or [])[:limit]:
            critique_status = str(item.get("hypothesis_critique_status") or "weak")
            feedback_action = "drop_hypothesis_pattern"
            if critique_status == "strong":
                feedback_action = "retain_hypothesis_pattern"
                retain_count += 1
            elif critique_status == "watch":
                feedback_action = "revise_hypothesis_pattern"
                revise_count += 1
            else:
                drop_count += 1
            items.append(
                {
                    "brief_id": item.get("brief_id"),
                    "expression_id": item.get("expression_id"),
                    "alpha_family": item.get("alpha_family"),
                    "regime_bias": item.get("regime_bias"),
                    "hypothesis_critique_status": critique_status,
                    "hypothesis_critique_score": item.get("hypothesis_critique_score"),
                    "feedback_action": feedback_action,
                    "feedback_priority": "high" if critique_status == "watch" else ("medium" if critique_status == "weak" else "low"),
                }
            )
        return {
            "status": "ok",
            "current_regime": critique.get("current_regime"),
            "items": items,
            "alpha_hypothesis_feedback_queue_summary": {
                "queue_count": len(items),
                "revise_count": revise_count,
                "retain_count": retain_count,
                "drop_count": drop_count,
                "system_alpha_feedback_queue_action": "prioritize_watch_hypotheses_for_revision" if revise_count > 0 else "retain_only_strong_hypothesis_patterns",
            },
            "as_of": critique.get("as_of"),
        }

    def alpha_hypothesis_prompt_tuning_latest(self, limit: int = 20) -> dict:
        queue = self.alpha_hypothesis_feedback_queue_latest(limit=max(limit, 4))
        items = []
        tighten_count = 0
        relax_count = 0
        preserve_count = 0
        for item in list(queue.get("items") or [])[:limit]:
            action = str(item.get("feedback_action") or "drop_hypothesis_pattern")
            tuning_action = "tighten_constraints"
            tuning_reason = "low_critique_quality"
            if action == "retain_hypothesis_pattern":
                tuning_action = "preserve_constraints"
                tuning_reason = "strong_translation_pattern"
                preserve_count += 1
            elif action == "revise_hypothesis_pattern":
                tuning_action = "rebalance_constraints"
                tuning_reason = "watch_translation_pattern"
                relax_count += 1
            else:
                tighten_count += 1
            items.append(
                {
                    **item,
                    "prompt_tuning_action": tuning_action,
                    "prompt_tuning_reason": tuning_reason,
                    "target_constraint_shift": (
                        "favor_regime_matched_features"
                        if tuning_action == "rebalance_constraints"
                        else ("keep_current_prompt_shape" if tuning_action == "preserve_constraints" else "reduce_low_value_operator_mix")
                    ),
                }
            )
        return {
            "status": "ok",
            "current_regime": queue.get("current_regime"),
            "items": items,
            "alpha_hypothesis_prompt_tuning_summary": {
                "recommendation_count": len(items),
                "tighten_count": tighten_count,
                "rebalance_count": relax_count,
                "preserve_count": preserve_count,
                "system_alpha_prompt_tuning_action": "apply_hypothesis_prompt_tuning_feedback",
            },
            "as_of": queue.get("as_of"),
        }

    def alpha_synthesis_policy_updates_latest(self, limit: int = 20) -> dict:
        tuning = self.alpha_hypothesis_prompt_tuning_latest(limit=max(limit, 4))
        items = []
        for item in list(tuning.get("items") or [])[:limit]:
            tuning_action = str(item.get("prompt_tuning_action") or "tighten_constraints")
            operator_policy = "reduce_operator_entropy"
            feature_policy = "concentrate_on_regime_fit"
            if tuning_action == "preserve_constraints":
                operator_policy = "preserve_operator_mix"
                feature_policy = "preserve_feature_mix"
            elif tuning_action == "rebalance_constraints":
                operator_policy = "rebalance_operator_mix"
                feature_policy = "increase_regime_matched_features"
            items.append(
                {
                    "brief_id": item.get("brief_id"),
                    "alpha_family": item.get("alpha_family"),
                    "regime_bias": item.get("regime_bias"),
                    "prompt_tuning_action": tuning_action,
                    "operator_policy_update": operator_policy,
                    "feature_policy_update": feature_policy,
                    "policy_update_scope": "hypothesis_generator",
                }
            )
        return {
            "status": "ok",
            "current_regime": tuning.get("current_regime"),
            "items": items,
            "alpha_synthesis_policy_updates_summary": {
                "update_count": len(items),
                "generator_policy_scope": "hypothesis_generator",
                "system_alpha_policy_update_action": "apply_synthesis_feedback_policy_updates",
            },
            "as_of": tuning.get("as_of"),
        }

    def alpha_feedback_learning_state_latest(self, limit: int = 20) -> dict:
        queue = self.alpha_hypothesis_feedback_queue_latest(limit=max(limit, 4))
        tuning = self.alpha_hypothesis_prompt_tuning_latest(limit=max(limit, 4))
        updates = self.alpha_synthesis_policy_updates_latest(limit=max(limit, 4))
        queue_summary = queue.get("alpha_hypothesis_feedback_queue_summary") or {}
        tuning_summary = tuning.get("alpha_hypothesis_prompt_tuning_summary") or {}
        update_summary = updates.get("alpha_synthesis_policy_updates_summary") or {}
        learning_state = "active_feedback_learning"
        if int(queue_summary.get("queue_count", 0) or 0) == 0:
            learning_state = "idle_feedback_learning"
        elif int(queue_summary.get("drop_count", 0) or 0) > int(queue_summary.get("retain_count", 0) or 0):
            learning_state = "corrective_feedback_learning"
        return {
            "status": "ok",
            "current_regime": queue.get("current_regime"),
            "feedback_learning_state": {
                "learning_state": learning_state,
                "feedback_queue_count": int(queue_summary.get("queue_count", 0) or 0),
                "prompt_tuning_count": int(tuning_summary.get("recommendation_count", 0) or 0),
                "policy_update_count": int(update_summary.get("update_count", 0) or 0),
                "system_alpha_feedback_learning_action": "feed_critique_outcomes_back_into_hypothesis_generator",
            },
            "as_of": queue.get("as_of"),
        }

    def alpha_feedback_optimization_effectiveness_latest(self, limit: int = 20) -> dict:
        queue = self.alpha_hypothesis_feedback_queue_latest(limit=max(limit, 4))
        tuning = self.alpha_hypothesis_prompt_tuning_latest(limit=max(limit, 4))
        state = self.alpha_feedback_learning_state_latest(limit=max(limit, 4))
        hypothesis_effectiveness = self.alpha_hypothesis_effectiveness_latest(limit=max(limit, 4))
        queue_summary = queue.get("alpha_hypothesis_feedback_queue_summary") or {}
        tuning_summary = tuning.get("alpha_hypothesis_prompt_tuning_summary") or {}
        hypo_payload = hypothesis_effectiveness.get("alpha_hypothesis_effectiveness") or {}
        effectiveness_status = "effective"
        if str(hypo_payload.get("effectiveness_status") or "") == "insufficient":
            effectiveness_status = "insufficient"
        elif int(queue_summary.get("revise_count", 0) or 0) > int(tuning_summary.get("preserve_count", 0) or 0):
            effectiveness_status = "watch"
        return {
            "status": "ok",
            "current_regime": queue.get("current_regime"),
            "alpha_feedback_optimization_effectiveness": {
                "effectiveness_status": effectiveness_status,
                "feedback_queue_count": int(queue_summary.get("queue_count", 0) or 0),
                "policy_update_count": int((state.get("feedback_learning_state") or {}).get("policy_update_count", 0) or 0),
                "strong_candidate_count": int(hypo_payload.get("strong_candidate_count", 0) or 0),
                "system_alpha_feedback_optimization_action": (
                    "tighten_feedback_learning_loop"
                    if effectiveness_status == "insufficient"
                    else ("monitor_feedback_revisions" if effectiveness_status == "watch" else "continue_feedback_optimized_hypothesis_generation")
                ),
            },
            "source_packets": {
                "alpha_synthesis_structural_discovery_intelligence": "ASD-05",
                "alpha_synthesis_structural_discovery_intelligence_hypothesis": "ASD-04",
            },
            "as_of": queue.get("as_of"),
        }
