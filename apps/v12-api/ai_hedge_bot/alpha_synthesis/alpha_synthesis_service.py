from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.alpha_synthesis.aae_bridge import AlphaSynthesisAAEBridge
from ai_hedge_bot.alpha_synthesis.dsl.expression import AlphaExpression
from ai_hedge_bot.alpha_synthesis.dsl.validator import validate_expression
from ai_hedge_bot.alpha_synthesis.evaluation.expression_evaluator import ExpressionEvaluator
from ai_hedge_bot.alpha_synthesis.generators.random_generator import RandomAlphaGenerator
from ai_hedge_bot.alpha_synthesis.novelty.structural_novelty import score_structural_novelty
from ai_hedge_bot.alpha_synthesis.repositories.expression_repository import ExpressionRepository
from ai_hedge_bot.alpha_synthesis.repositories.synthesis_run_repository import SynthesisRunRepository
from ai_hedge_bot.alpha_synthesis.validation.semantic_prescreen import semantic_prescreen
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id, new_run_id


class AlphaSynthesisService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.generator = RandomAlphaGenerator(seed=101)
        self.evaluator = ExpressionEvaluator()
        self.expressions = ExpressionRepository()
        self.runs = SynthesisRunRepository()
        self.aae_bridge = AlphaSynthesisAAEBridge()

    def _ensure_recent_run(self, requested_count: int = 6) -> dict:
        latest = self.runs.latest_run()
        recent_candidates = self.runs.list_recent_candidates(limit=5)
        if latest and recent_candidates:
            return latest

        started_at = utc_now_iso()
        run_id = new_run_id()
        library_rows = self.expressions.list_recent_expressions(limit=200)
        generated = 0
        accepted = 0
        rejected = 0
        for expr in self.generator.generate_batch(requested_count, config={"max_depth": 4}):
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
                {"generator_type": "random", "parent_expression_ids": [], "status": status},
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
                    "generator_type": "random",
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
                "generator_type": "random",
                "config_json": self.store.to_json({"requested_count": requested_count, "max_depth": 4}),
                "requested_count": requested_count,
                "generated_count": generated,
                "accepted_count": accepted,
                "rejected_count": rejected,
                "started_at": started_at,
                "completed_at": completed_at,
                "status": "ok",
            }
        )
        return self.runs.latest_run()

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
