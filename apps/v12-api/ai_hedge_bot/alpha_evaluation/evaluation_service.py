from __future__ import annotations

from ai_hedge_bot.alpha_evaluation.candidate_loader import AlphaCandidateLoader
from ai_hedge_bot.alpha_evaluation.correlation_filter import CorrelationFilter
from ai_hedge_bot.alpha_evaluation.cost_adjuster import CostAdjuster
from ai_hedge_bot.alpha_evaluation.decay_detector import DecayDetector
from ai_hedge_bot.alpha_evaluation.forward_return_engine import ForwardReturnEngine
from ai_hedge_bot.alpha_evaluation.overfit_detector import OverfitDetector
from ai_hedge_bot.alpha_evaluation.robustness_engine import RobustnessEngine
from ai_hedge_bot.alpha_evaluation.selection_engine import AlphaSelectionEngine
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id, new_run_id


class AlphaEvaluationService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.loader = AlphaCandidateLoader()
        self.forward_return_engine = ForwardReturnEngine()
        self.cost_adjuster = CostAdjuster()
        self.decay_detector = DecayDetector()
        self.robustness_engine = RobustnessEngine()
        self.overfit_detector = OverfitDetector()
        self.correlation_filter = CorrelationFilter()
        self.selection_engine = AlphaSelectionEngine()

    def run(self, limit: int = 20) -> dict:
        latest_run = self._latest_run()
        if latest_run:
            return self.latest(limit=limit)

        candidates = self.loader.load_latest_candidates(limit=max(limit, 10))
        run_id = new_run_id()
        started_at = utc_now_iso()
        score_rows: list[dict] = []
        forward_rows: list[dict] = []
        promoted = 0
        rejected = 0

        for candidate in candidates:
            raw_rows = self.forward_return_engine.compute(candidate)
            adjusted_rows, turnover, cost_penalty = self.cost_adjuster.apply(candidate, raw_rows)
            sample_count = 120 + (candidate.feature_count * 20) + (candidate.operator_count * 15)
            robustness = self.robustness_engine.evaluate(adjusted_rows)
            decay = self.decay_detector.analyze(adjusted_rows)
            redundancy = self.correlation_filter.evaluate(candidate, peer_count=len(candidates))
            overfit_risk = self.overfit_detector.evaluate(candidate, sample_count=sample_count, mean_return=robustness["mean_return"])
            final_score = (
                (0.35 * max(robustness["sharpe_final"], 0.0))
                + (0.20 * robustness["robustness_score"])
                + (0.15 * decay["decay_score"])
                + (0.20 * (1 - min(overfit_risk, 1.0)))
                + (0.10 * (1 - min(redundancy["redundancy_score"], 1.0)))
            )
            metrics = {
                "sample_count": sample_count,
                "cost_adjusted_mean_return": robustness["mean_return"],
                "hit_rate": robustness["hit_rate"],
                "sharpe_final": robustness["sharpe_final"],
                "decay_score": decay["decay_score"],
                "overfit_risk": overfit_risk,
                "redundancy_score": redundancy["redundancy_score"],
                "correlation_estimate": redundancy["correlation_estimate"],
                "final_score": round(final_score, 6),
            }
            decision = self.selection_engine.decide(metrics)
            if decision == "promote_candidate":
                promoted += 1
            elif decision.startswith("reject"):
                rejected += 1

            now = utc_now_iso()
            for row in adjusted_rows:
                forward_rows.append(
                    {
                        "run_id": run_id,
                        "alpha_id": candidate.alpha_id,
                        "horizon": row["horizon"],
                        "raw_forward_return": row["raw_forward_return"],
                        "cost_adjusted_return": row["cost_adjusted_return"],
                        "created_at": now,
                    }
                )

            score_rows.append(
                {
                    "run_id": run_id,
                    "alpha_id": candidate.alpha_id,
                    "mean_return": robustness["mean_return"],
                    "median_return": robustness["median_return"],
                    "hit_rate": robustness["hit_rate"],
                    "sharpe_like": robustness["sharpe_like"],
                    "sharpe_robust": robustness["sharpe_robust"],
                    "sharpe_final": robustness["sharpe_final"],
                    "turnover": turnover,
                    "cost_penalty": cost_penalty,
                    "decay_score": decay["decay_score"],
                    "robustness_score": robustness["robustness_score"],
                    "overfit_risk": overfit_risk,
                    "redundancy_score": redundancy["redundancy_score"],
                    "final_score": round(final_score, 6),
                    "decision": decision,
                    "details_json": self.store.to_json(
                        {
                            "formula": candidate.formula,
                            "alpha_family": candidate.alpha_family,
                            "sample_count": sample_count,
                            "correlation_estimate": redundancy["correlation_estimate"],
                            "decay_status": decay["decay_status"],
                        }
                    ),
                    "created_at": now,
                }
            )

        self.store.append(
            "alpha_evaluation_runs",
            {
                "run_id": run_id,
                "started_at": started_at,
                "completed_at": utc_now_iso(),
                "candidate_count": len(candidates),
                "evaluated_count": len(score_rows),
                "promoted_count": promoted,
                "rejected_count": rejected,
                "status": "ok",
            },
        )
        if forward_rows:
            self.store.append("alpha_forward_returns", forward_rows)
        if score_rows:
            self.store.append("alpha_evaluation_scores", score_rows)
        return self.latest(limit=limit)

    def _latest_run(self) -> dict:
        return self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_evaluation_runs
            ORDER BY completed_at DESC, started_at DESC
            LIMIT 1
            """
        ) or {}

    def _latest_scores(self, limit: int = 50) -> list[dict]:
        rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_evaluation_scores
            ORDER BY created_at DESC, alpha_id ASC
            LIMIT ?
            """,
            [max(int(limit), 1)],
        )
        for row in rows:
            row["details"] = self.store.parse_json(row.get("details_json"), {}) or {}
        return rows

    def _latest_forward_returns(self, limit: int = 100) -> list[dict]:
        return self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_forward_returns
            ORDER BY created_at DESC, alpha_id ASC
            LIMIT ?
            """,
            [max(int(limit), 1)],
        )

    def latest(self, limit: int = 20) -> dict:
        run = self._latest_run()
        if not run:
            return self.run(limit=limit)
        scores = self._latest_scores(limit=max(limit * 3, 30))
        items = []
        for row in scores[:limit]:
            details = dict(row.get("details") or {})
            items.append(
                {
                    "alpha_id": row.get("alpha_id"),
                    "alpha_family": details.get("alpha_family"),
                    "formula": details.get("formula"),
                    "mean_return": row.get("mean_return"),
                    "hit_rate": row.get("hit_rate"),
                    "sharpe_final": row.get("sharpe_final"),
                    "final_score": row.get("final_score"),
                    "decision": row.get("decision"),
                }
            )
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "items": items,
            "alpha_evaluation_summary": {
                "candidate_count": len(items),
                "promote_candidate_count": sum(1 for item in items if item.get("decision") == "promote_candidate"),
                "watchlist_count": sum(1 for item in items if item.get("decision") == "watchlist"),
                "reject_count": sum(1 for item in items if str(item.get("decision") or "").startswith("reject")),
                "system_alpha_evaluation_action": "run_selection_gate_before_promotion",
            },
            "as_of": run.get("completed_at"),
        }

    def alpha_decay_analysis_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        scores = self._latest_scores(limit=max(limit * 3, 30))
        items = []
        for row in scores[:limit]:
            details = dict(row.get("details") or {})
            decay_score = float(row.get("decay_score", 0.0) or 0.0)
            items.append(
                {
                    "alpha_id": row.get("alpha_id"),
                    "alpha_family": details.get("alpha_family"),
                    "decay_score": decay_score,
                    "decay_status": details.get("decay_status") or ("stable" if decay_score >= 0.8 else "moderate"),
                    "selection_decision": row.get("decision"),
                }
            )
        return {
            "status": "ok",
            "items": items,
            "alpha_decay_analysis_summary": {
                "alpha_count": len(items),
                "decayed_count": sum(1 for item in items if str(item.get("decay_status")) in {"moderate", "severe"}),
                "system_alpha_decay_action": "filter_decayed_alpha_before_promotion",
            },
        }

    def alpha_correlation_matrix_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        scores = self._latest_scores(limit=max(limit * 3, 30))
        items = []
        for row in scores[:limit]:
            details = dict(row.get("details") or {})
            corr = float(details.get("correlation_estimate", 0.0) or 0.0)
            items.append(
                {
                    "alpha_id": row.get("alpha_id"),
                    "alpha_family": details.get("alpha_family"),
                    "correlation_estimate": corr,
                    "redundancy_score": row.get("redundancy_score"),
                    "redundancy_status": "hard_reject" if corr >= 0.92 else ("watch" if corr >= 0.80 else "ok"),
                }
            )
        return {
            "status": "ok",
            "items": items,
            "alpha_correlation_matrix_summary": {
                "alpha_count": len(items),
                "hard_reject_count": sum(1 for item in items if item.get("redundancy_status") == "hard_reject"),
                "watch_count": sum(1 for item in items if item.get("redundancy_status") == "watch"),
                "system_alpha_correlation_action": "prevent_redundant_alpha_promotion",
            },
        }

    def alpha_robustness_ranking_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        scores = self._latest_scores(limit=max(limit * 3, 30))
        items = []
        for row in scores[:limit]:
            details = dict(row.get("details") or {})
            items.append(
                {
                    "alpha_id": row.get("alpha_id"),
                    "alpha_family": details.get("alpha_family"),
                    "robustness_score": row.get("robustness_score"),
                    "sharpe_final": row.get("sharpe_final"),
                    "overfit_risk": row.get("overfit_risk"),
                    "rank_reason": "higher_cost_adjusted_stability",
                }
            )
        items.sort(key=lambda item: (-float(item.get("robustness_score") or 0.0), -float(item.get("sharpe_final") or 0.0)))
        return {
            "status": "ok",
            "items": items[:limit],
            "alpha_robustness_ranking_summary": {
                "alpha_count": min(len(items), limit),
                "strong_count": sum(1 for item in items[:limit] if float(item.get("robustness_score") or 0.0) >= 0.6),
                "system_alpha_robustness_action": "promote_only_stable_alpha_candidates",
            },
        }

    def alpha_selection_decisions_latest(self, limit: int = 20) -> dict:
        latest = self.latest(limit=limit)
        return {
            "status": "ok",
            "run_id": latest.get("run_id"),
            "items": [
                {
                    "alpha_id": item.get("alpha_id"),
                    "decision": item.get("decision"),
                    "final_score": item.get("final_score"),
                    "selection_action": (
                        "queue_for_aae_promotion"
                        if item.get("decision") == "promote_candidate"
                        else ("keep_under_watch" if item.get("decision") == "watchlist" else "reject_from_promotion")
                    ),
                }
                for item in list(latest.get("items") or [])[:limit]
            ],
            "alpha_selection_decisions_summary": {
                "alpha_count": len(list(latest.get("items") or [])[:limit]),
                "promote_candidate_count": sum(1 for item in list(latest.get("items") or [])[:limit] if item.get("decision") == "promote_candidate"),
                "watchlist_count": sum(1 for item in list(latest.get("items") or [])[:limit] if item.get("decision") == "watchlist"),
                "system_alpha_selection_action": "send_only_selected_alpha_to_promotion_flow",
            },
        }

    def alpha_evaluation_candidate(self, alpha_id: str) -> dict:
        self.latest(limit=20)
        row = self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_evaluation_scores
            WHERE alpha_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [alpha_id],
        ) or {}
        details = self.store.parse_json(row.get("details_json"), {}) or {}
        returns = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_forward_returns
            WHERE alpha_id=?
            ORDER BY created_at DESC, horizon ASC
            LIMIT 20
            """,
            [alpha_id],
        )
        return {
            "status": "ok" if row else "not_found",
            "alpha_id": alpha_id,
            "formula": details.get("formula"),
            "alpha_family": details.get("alpha_family"),
            "sample_count": details.get("sample_count"),
            "decision": row.get("decision"),
            "final_score": row.get("final_score"),
            "decay_score": row.get("decay_score"),
            "overfit_risk": row.get("overfit_risk"),
            "redundancy_score": row.get("redundancy_score"),
            "forward_returns": returns,
        }
