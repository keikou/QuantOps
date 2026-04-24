from __future__ import annotations

from ai_hedge_bot.alpha_ensemble.diversification_scorer import DiversificationScorer
from ai_hedge_bot.alpha_ensemble.ensemble_candidate_generator import EnsembleCandidateGenerator
from ai_hedge_bot.alpha_ensemble.ensemble_correlation_engine import EnsembleCorrelationEngine
from ai_hedge_bot.alpha_ensemble.ensemble_scoring_engine import EnsembleScoringEngine
from ai_hedge_bot.alpha_ensemble.ensemble_selection_engine import EnsembleSelectionEngine
from ai_hedge_bot.alpha_ensemble.ensemble_weight_allocator import EnsembleWeightAllocator
from ai_hedge_bot.alpha_ensemble.marginal_contribution_engine import MarginalContributionEngine
from ai_hedge_bot.alpha_ensemble.validated_alpha_loader import ValidatedAlphaLoader
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id


class AlphaEnsembleService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.loader = ValidatedAlphaLoader()
        self.generator = EnsembleCandidateGenerator()
        self.correlation_engine = EnsembleCorrelationEngine()
        self.marginal_engine = MarginalContributionEngine()
        self.diversification = DiversificationScorer()
        self.scoring = EnsembleScoringEngine()
        self.weight_allocator = EnsembleWeightAllocator()
        self.selection = EnsembleSelectionEngine()

    def _latest_run(self) -> dict:
        return self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_ensemble_runs
            ORDER BY completed_at DESC, started_at DESC
            LIMIT 1
            """
        ) or {}

    def _latest_rows(self, table: str, limit: int = 100) -> list[dict]:
        return self.store.fetchall_dict(
            f"""
            SELECT *
            FROM {table}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [max(int(limit), 1)],
        )

    def _build_latest_payload(self, run: dict, limit: int = 20) -> dict:
        score_rows = self._latest_rows("alpha_ensemble_scores", limit=max(limit * 3, 30))
        items = []
        for row in score_rows[:limit]:
            selection = self.store.fetchone_dict(
                """
                SELECT *
                FROM alpha_ensemble_selection
                WHERE run_id=? AND ensemble_id=?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                [run.get("run_id"), row.get("ensemble_id")],
            ) or {}
            items.append(
                {
                    "ensemble_id": row.get("ensemble_id"),
                    "alpha_count": row.get("alpha_count"),
                    "final_ensemble_score": row.get("final_ensemble_score"),
                    "diversification_score": row.get("diversification_score"),
                    "decision": row.get("decision"),
                    "portfolio_ready": selection.get("portfolio_ready"),
                }
            )
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "items": items,
            "alpha_ensemble_summary": {
                "validated_alpha_count": run.get("validated_alpha_count"),
                "candidate_ensemble_count": run.get("candidate_ensemble_count"),
                "portfolio_ready_count": sum(1 for item in items if item.get("portfolio_ready")),
                "system_alpha_ensemble_action": "select_portfolio_ready_alpha_combinations_only",
            },
            "as_of": run.get("completed_at"),
        }

    def _materialize_run(self, limit: int = 20) -> dict:
        alphas = self.loader.load_validated_alphas(limit=max(limit, 8))
        alpha_by_id = {alpha.alpha_id: alpha for alpha in alphas}
        candidates = self.generator.generate(alphas, limit=max(limit, 5))
        run_id = new_run_id()
        started_at = utc_now_iso()

        candidate_rows: list[dict] = []
        correlation_rows: list[dict] = []
        marginal_rows: list[dict] = []
        score_rows: list[dict] = []
        weight_rows: list[dict] = []
        selection_rows: list[dict] = []

        selected_alpha_count = 0
        best_score = 0.0

        for candidate in candidates:
            selected_alphas = [alpha_by_id[alpha_id] for alpha_id in candidate.alpha_ids if alpha_id in alpha_by_id]
            ensemble_corr = self.correlation_engine.compute(selected_alphas)
            diversification = self.diversification.score(candidate.alpha_ids, alpha_by_id, ensemble_corr)
            marginal = self.marginal_engine.compute(candidate.alpha_ids, alpha_by_id, ensemble_corr)
            score = self.scoring.score(candidate.alpha_ids, alpha_by_id, diversification, marginal)
            weights = self.weight_allocator.allocate(candidate.alpha_ids, alpha_by_id, marginal, ensemble_corr)
            decision, reason, portfolio_ready = self.selection.decide(score, ensemble_corr, weights)
            best_score = max(best_score, float(score.get("final_ensemble_score", 0.0) or 0.0))
            if portfolio_ready:
                selected_alpha_count = max(selected_alpha_count, len(candidate.alpha_ids))
            now = utc_now_iso()

            candidate_rows.append(
                {
                    "run_id": run_id,
                    "ensemble_id": candidate.ensemble_id,
                    "alpha_ids": self.store.to_json(candidate.alpha_ids),
                    "alpha_count": len(candidate.alpha_ids),
                    "source": candidate.source,
                    "created_at": now,
                }
            )

            for row in ensemble_corr:
                correlation_rows.append(
                    {
                        "run_id": run_id,
                        "ensemble_id": candidate.ensemble_id,
                        "alpha_id_a": row["alpha_id_a"],
                        "alpha_id_b": row["alpha_id_b"],
                        "correlation": row["correlation"],
                        "overlap_score": row["overlap_score"],
                        "hard_redundant": row["hard_redundant"],
                        "created_at": now,
                    }
                )
            for row in marginal:
                marginal_rows.append(
                    {
                        "run_id": run_id,
                        "ensemble_id": candidate.ensemble_id,
                        "alpha_id": row["alpha_id"],
                        "contribution_to_return": row["contribution_to_return"],
                        "contribution_to_risk": row["contribution_to_risk"],
                        "contribution_to_sharpe": row["contribution_to_sharpe"],
                        "contribution_to_diversification": row["contribution_to_diversification"],
                        "marginal_score": row["marginal_score"],
                        "created_at": now,
                    }
                )
            score_rows.append(
                {
                    "run_id": run_id,
                    "ensemble_id": candidate.ensemble_id,
                    "alpha_count": len(candidate.alpha_ids),
                    "expected_return_score": score["expected_return_score"],
                    "expected_risk_score": score["expected_risk_score"],
                    "sharpe_score": score["sharpe_score"],
                    "diversification_score": score["diversification_score"],
                    "stability_score": score["stability_score"],
                    "capacity_score": score["capacity_score"],
                    "concentration_penalty": score["concentration_penalty"],
                    "final_ensemble_score": score["final_ensemble_score"],
                    "decision": decision,
                    "reject_reason": "" if portfolio_ready else reason,
                    "created_at": now,
                }
            )
            for row in weights:
                weight_rows.append(
                    {
                        "run_id": run_id,
                        "ensemble_id": candidate.ensemble_id,
                        "alpha_id": row["alpha_id"],
                        "raw_weight": row["raw_weight"],
                        "normalized_weight": row["normalized_weight"],
                        "cap_adjusted_weight": row["cap_adjusted_weight"],
                        "final_weight": row["final_weight"],
                        "weight_reason": row["weight_reason"],
                        "created_at": now,
                    }
                )
            selection_rows.append(
                {
                    "selection_id": f"{run_id}.{candidate.ensemble_id}",
                    "run_id": run_id,
                    "ensemble_id": candidate.ensemble_id,
                    "selected": portfolio_ready,
                    "selected_alpha_ids": self.store.to_json(candidate.alpha_ids),
                    "portfolio_ready": portfolio_ready,
                    "reason": reason,
                    "payload_json": self.store.to_json(
                        {
                            "source": "AES-03",
                            "run_id": run_id,
                            "ensemble_id": candidate.ensemble_id,
                            "portfolio_ready": portfolio_ready,
                            "ensemble_score": score["final_ensemble_score"],
                            "alphas": [
                                {
                                    "alpha_id": row["alpha_id"],
                                    "weight": row["final_weight"],
                                    "score": alpha_by_id[row["alpha_id"]].aes_score,
                                    "capacity_score": alpha_by_id[row["alpha_id"]].capacity_score,
                                    "risk_flags": [],
                                }
                                for row in weights
                            ],
                        }
                    ),
                    "created_at": now,
                }
            )

        self.store.append(
            "alpha_ensemble_runs",
            {
                "run_id": run_id,
                "started_at": started_at,
                "completed_at": utc_now_iso(),
                "validated_alpha_count": len(alphas),
                "candidate_ensemble_count": len(candidate_rows),
                "selected_alpha_count": selected_alpha_count,
                "portfolio_score": round(best_score, 6),
                "status": "ok",
                "notes": "aes03_alpha_ensemble_selection",
            },
        )
        if candidate_rows:
            self.store.append("alpha_ensemble_candidates", candidate_rows)
        if correlation_rows:
            self.store.append("alpha_ensemble_correlations", correlation_rows)
        if marginal_rows:
            self.store.append("alpha_marginal_contributions", marginal_rows)
        if score_rows:
            self.store.append("alpha_ensemble_scores", score_rows)
        if weight_rows:
            self.store.append("alpha_ensemble_weights", weight_rows)
        if selection_rows:
            self.store.append("alpha_ensemble_selection", selection_rows)
        run = self._latest_run()
        return self._build_latest_payload(run, limit=limit)

    def run(self, limit: int = 20) -> dict:
        latest_run = self._latest_run()
        if latest_run:
            latest = self.latest(limit=limit)
            if list(latest.get("items") or []):
                return latest
        return self._materialize_run(limit=limit)

    def latest(self, limit: int = 20) -> dict:
        run = self._latest_run()
        if not run:
            return self.run(limit=limit)
        score_rows = self._latest_rows("alpha_ensemble_scores", limit=max(limit * 3, 30))
        if not score_rows:
            return self._materialize_run(limit=limit)
        return self._build_latest_payload(run, limit=limit)

    def alpha_ensemble_candidates_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_ensemble_candidates", limit=max(limit * 3, 30))
        items = []
        for row in rows[:limit]:
            items.append(
                {
                    "ensemble_id": row.get("ensemble_id"),
                    "alpha_ids": self.store.parse_json(row.get("alpha_ids"), []) or [],
                    "alpha_count": row.get("alpha_count"),
                    "source": row.get("source"),
                }
            )
        return {"status": "ok", "items": items}

    def alpha_ensemble_candidate(self, ensemble_id: str) -> dict:
        self.latest(limit=20)
        candidate = self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_ensemble_candidates
            WHERE ensemble_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [ensemble_id],
        ) or {}
        score = self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_ensemble_scores
            WHERE ensemble_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [ensemble_id],
        ) or {}
        weights = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_ensemble_weights
            WHERE ensemble_id=?
            ORDER BY final_weight DESC, alpha_id ASC
            LIMIT 20
            """,
            [ensemble_id],
        )
        return {
            "status": "ok" if candidate else "not_found",
            "ensemble_id": ensemble_id,
            "alpha_ids": self.store.parse_json(candidate.get("alpha_ids"), []) or [],
            "source": candidate.get("source"),
            "score": score,
            "weights": weights,
        }

    def alpha_ensemble_correlation_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_ensemble_correlations", limit=max(limit * 4, 40))
        items = [
            {
                "ensemble_id": row.get("ensemble_id"),
                "alpha_id_a": row.get("alpha_id_a"),
                "alpha_id_b": row.get("alpha_id_b"),
                "correlation": row.get("correlation"),
                "hard_redundant": row.get("hard_redundant"),
            }
            for row in rows[:limit]
        ]
        return {
            "status": "ok",
            "items": items,
            "alpha_ensemble_correlation_summary": {
                "pair_count": len(items),
                "hard_redundant_count": sum(1 for item in items if item.get("hard_redundant")),
                "system_alpha_ensemble_correlation_action": "reject_hard_redundant_alpha_pairs",
            },
        }

    def alpha_marginal_contribution_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_marginal_contributions", limit=max(limit * 4, 40))
        items = [
            {
                "ensemble_id": row.get("ensemble_id"),
                "alpha_id": row.get("alpha_id"),
                "marginal_score": row.get("marginal_score"),
                "contribution_to_sharpe": row.get("contribution_to_sharpe"),
                "contribution_to_diversification": row.get("contribution_to_diversification"),
            }
            for row in rows[:limit]
        ]
        return {
            "status": "ok",
            "items": items,
            "alpha_marginal_contribution_summary": {
                "alpha_count": len(items),
                "positive_marginal_count": sum(1 for item in items if float(item.get("marginal_score", 0.0) or 0.0) > 0.0),
                "system_alpha_marginal_action": "prune_low_contribution_alpha_from_ensemble",
            },
        }

    def alpha_ensemble_selection_latest(self, limit: int = 20) -> dict:
        latest = self.latest(limit=limit)
        rows = self._latest_rows("alpha_ensemble_selection", limit=max(limit * 3, 30))
        items = [
            {
                "ensemble_id": row.get("ensemble_id"),
                "selected": row.get("selected"),
                "portfolio_ready": row.get("portfolio_ready"),
                "reason": row.get("reason"),
                "selected_alpha_ids": self.store.parse_json(row.get("selected_alpha_ids"), []) or [],
            }
            for row in rows[:limit]
        ]
        return {
            "status": "ok",
            "run_id": latest.get("run_id"),
            "items": items,
            "alpha_ensemble_selection_summary": {
                "selection_count": len(items),
                "portfolio_ready_count": sum(1 for item in items if item.get("portfolio_ready")),
                "system_alpha_ensemble_selection_action": "stage_only_portfolio_ready_ensemble_for_mpi_lcc",
            },
        }

    def alpha_ensemble_weights_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_ensemble_weights", limit=max(limit * 4, 40))
        items = [
            {
                "ensemble_id": row.get("ensemble_id"),
                "alpha_id": row.get("alpha_id"),
                "final_weight": row.get("final_weight"),
                "cap_adjusted_weight": row.get("cap_adjusted_weight"),
                "weight_reason": row.get("weight_reason"),
            }
            for row in rows[:limit]
        ]
        return {
            "status": "ok",
            "items": items,
            "alpha_ensemble_weights_summary": {
                "weight_count": len(items),
                "system_alpha_ensemble_weight_action": "emit_conservative_initial_alpha_weights",
            },
        }
