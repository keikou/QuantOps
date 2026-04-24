from __future__ import annotations

from ai_hedge_bot.alpha_evaluation.evaluation_service import AlphaEvaluationService
from ai_hedge_bot.alpha_validation.oos_evaluator import OOSEvaluator
from ai_hedge_bot.alpha_validation.stability_analyzer import StabilityAnalyzer
from ai_hedge_bot.alpha_validation.validation_decision_engine import ValidationDecisionEngine
from ai_hedge_bot.alpha_validation.walk_forward_engine import WalkForwardEngine
from ai_hedge_bot.alpha_validation.window_builder import WindowBuilder
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id


class AlphaValidationService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.evaluation = AlphaEvaluationService()
        self.window_builder = WindowBuilder()
        self.walk_forward = WalkForwardEngine()
        self.oos = OOSEvaluator()
        self.stability = StabilityAnalyzer()
        self.decision = ValidationDecisionEngine()

    @staticmethod
    def _fallback_candidates() -> list[dict]:
        return [
            {
                "alpha_id": "alpha.synthetic.validation",
                "alpha_family": "synthetic",
                "final_score": 0.66,
                "sharpe_final": 0.58,
                "hit_rate": 0.54,
                "decision": "watchlist",
            }
        ]

    def _materialize_run(self, limit: int = 20) -> dict:
        evaluation = self.evaluation.latest(limit=max(limit, 10))
        candidates = [
            item
            for item in list(evaluation.get("items") or [])
            if str(item.get("decision") or "") in {"promote_candidate", "watchlist"}
        ][: max(limit, 5)]
        if not candidates:
            candidates = list(evaluation.get("items") or [])[: max(limit, 5)]
        if not candidates:
            candidates = self._fallback_candidates()
        run_id = new_run_id()
        started_at = utc_now_iso()
        window_rows = []
        oos_rows = []
        summary_rows = []
        passed_count = 0
        failed_count = 0
        score_lookup = {str(item.get("alpha_id") or ""): item for item in list(evaluation.get("items") or [])}

        for candidate in candidates:
            alpha_id = str(candidate.get("alpha_id") or "")
            windows = self.window_builder.build(alpha_id=alpha_id, min_windows=4)
            per_window = []
            for idx, window in enumerate(windows):
                metrics = self.walk_forward.evaluate_window(
                    final_score=float(candidate.get("final_score", 0.0) or 0.0),
                    sharpe_final=float(candidate.get("sharpe_final", 0.0) or 0.0),
                    hit_rate=float(candidate.get("hit_rate", 0.0) or 0.0),
                    idx=idx,
                )
                oos_eval = self.oos.evaluate(metrics)
                now = utc_now_iso()
                window_rows.append(
                    {
                        "run_id": run_id,
                        "alpha_id": alpha_id,
                        "window_id": window["window_id"],
                        "train_start": window["train_start"],
                        "train_end": window["train_end"],
                        "test_start": window["test_start"],
                        "test_end": window["test_end"],
                        "symbol": window["symbol"],
                        "regime": window["regime"],
                        "created_at": now,
                    }
                )
                row = {
                    "run_id": run_id,
                    "alpha_id": alpha_id,
                    "window_id": window["window_id"],
                    "sample_count": metrics["sample_count"],
                    "train_score": metrics["train_score"],
                    "test_score": metrics["test_score"],
                    "train_sharpe": metrics["train_sharpe"],
                    "test_sharpe": metrics["test_sharpe"],
                    "train_hit_rate": metrics["train_hit_rate"],
                    "test_hit_rate": metrics["test_hit_rate"],
                    "score_gap": oos_eval["score_gap"],
                    "degradation_ratio": oos_eval["degradation_ratio"],
                    "passed": oos_eval["passed"],
                    "fail_reason": oos_eval["fail_reason"],
                    "created_at": now,
                }
                oos_rows.append(row)
                per_window.append(row)
            summary = self.stability.summarize(per_window)
            decision, reason, final_validation_score = self.decision.decide(summary)
            if decision == "validation_pass":
                passed_count += 1
            elif decision.startswith("validation_fail"):
                failed_count += 1
            summary_rows.append(
                {
                    "run_id": run_id,
                    "alpha_id": alpha_id,
                    "total_windows": summary["total_windows"],
                    "passed_windows": summary["passed_windows"],
                    "pass_rate": summary["pass_rate"],
                    "mean_oos_score": summary["mean_oos_score"],
                    "median_oos_score": summary["median_oos_score"],
                    "mean_degradation_ratio": summary["mean_degradation_ratio"],
                    "worst_window_score": summary["worst_window_score"],
                    "stability_score": summary["stability_score"],
                    "final_validation_score": final_validation_score,
                    "decision": decision,
                    "reason": reason,
                    "created_at": utc_now_iso(),
                }
            )

        self.store.append(
            "alpha_validation_runs",
            {
                "run_id": run_id,
                "started_at": started_at,
                "completed_at": utc_now_iso(),
                "candidate_count": len(candidates),
                "validated_count": len(summary_rows),
                "passed_count": passed_count,
                "failed_count": failed_count,
                "status": "ok",
                "notes": "aes02_walk_forward_validation",
            },
        )
        if window_rows:
            self.store.append("alpha_walk_forward_windows", window_rows)
        if oos_rows:
            self.store.append("alpha_oos_scores", oos_rows)
        if summary_rows:
            self.store.append("alpha_validation_summary", summary_rows)
        run = self._latest_run()
        items = self._latest_summary(limit=max(limit * 3, 30))[:limit]
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "items": items,
            "alpha_walk_forward_summary": {
                "candidate_count": len(items),
                "validation_pass_count": sum(1 for item in items if item.get("decision") == "validation_pass"),
                "validation_watchlist_count": sum(1 for item in items if item.get("decision") == "validation_watchlist"),
                "validation_fail_count": sum(1 for item in items if str(item.get("decision") or "").startswith("validation_fail")),
                "system_alpha_walk_forward_action": "require_oos_survival_before_promotion",
            },
            "as_of": run.get("completed_at"),
        }

    def run(self, limit: int = 20) -> dict:
        latest_run = self._latest_run()
        if latest_run:
            latest = self.latest(limit=limit)
            if list(latest.get("items") or []):
                return latest
        return self._materialize_run(limit=limit)

    def _latest_run(self) -> dict:
        return self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_validation_runs
            ORDER BY completed_at DESC, started_at DESC
            LIMIT 1
            """
        ) or {}

    def _latest_summary(self, limit: int = 100) -> list[dict]:
        return self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_validation_summary
            ORDER BY created_at DESC, alpha_id ASC
            LIMIT ?
            """,
            [max(int(limit), 1)],
        )

    def latest(self, limit: int = 20) -> dict:
        run = self._latest_run()
        if not run:
            return self.run(limit=limit)
        items = self._latest_summary(limit=max(limit * 3, 30))[:limit]
        if not items:
            return self._materialize_run(limit=limit)
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "items": items,
            "alpha_walk_forward_summary": {
                "candidate_count": len(items),
                "validation_pass_count": sum(1 for item in items if item.get("decision") == "validation_pass"),
                "validation_watchlist_count": sum(1 for item in items if item.get("decision") == "validation_watchlist"),
                "validation_fail_count": sum(1 for item in items if str(item.get("decision") or "").startswith("validation_fail")),
                "system_alpha_walk_forward_action": "require_oos_survival_before_promotion",
            },
            "as_of": run.get("completed_at"),
        }

    def alpha_oos_validation_latest(self, limit: int = 20) -> dict:
        latest = self.latest(limit=limit)
        return {
            "status": "ok",
            "run_id": latest.get("run_id"),
            "items": list(latest.get("items") or [])[:limit],
            "alpha_oos_validation_summary": {
                "alpha_count": len(list(latest.get("items") or [])[:limit]),
                "pass_count": sum(1 for item in list(latest.get("items") or [])[:limit] if item.get("decision") == "validation_pass"),
                "system_alpha_oos_action": "block_non_surviving_alpha_from_promotion",
            },
        }

    def alpha_validation_decisions_latest(self, limit: int = 20) -> dict:
        latest = self.latest(limit=limit)
        items = [
            {
                "alpha_id": item.get("alpha_id"),
                "decision": item.get("decision"),
                "final_validation_score": item.get("final_validation_score"),
                "validation_action": (
                    "production_promotable"
                    if item.get("decision") == "validation_pass"
                    else ("promotion_hold" if item.get("decision") == "validation_watchlist" else "validation_reject")
                ),
            }
            for item in list(latest.get("items") or [])[:limit]
        ]
        return {
            "status": "ok",
            "run_id": latest.get("run_id"),
            "items": items,
            "alpha_validation_decisions_summary": {
                "alpha_count": len(items),
                "production_promotable_count": sum(1 for item in items if item.get("validation_action") == "production_promotable"),
                "promotion_hold_count": sum(1 for item in items if item.get("validation_action") == "promotion_hold"),
                "validation_reject_count": sum(1 for item in items if item.get("validation_action") == "validation_reject"),
                "system_alpha_validation_action": "allow_only_validation_pass_to_enter_promotion_layer",
            },
        }

    def alpha_validation_failures_latest(self, limit: int = 20) -> dict:
        latest = self.latest(limit=limit)
        items = [
            item
            for item in list(latest.get("items") or [])
            if str(item.get("decision") or "").startswith("validation_fail")
        ][:limit]
        return {
            "status": "ok",
            "run_id": latest.get("run_id"),
            "items": items,
            "alpha_validation_failures_summary": {
                "failure_count": len(items),
                "system_alpha_failure_action": "recycle_failed_alpha_back_to_research_or_watchlist",
            },
        }

    def alpha_walk_forward_candidate(self, alpha_id: str) -> dict:
        self.latest(limit=20)
        summary = self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_validation_summary
            WHERE alpha_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [alpha_id],
        ) or {}
        windows = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_oos_scores
            WHERE alpha_id=?
            ORDER BY created_at DESC, window_id ASC
            LIMIT 20
            """,
            [alpha_id],
        )
        return {
            "status": "ok" if summary else "not_found",
            "alpha_id": alpha_id,
            "summary": summary,
            "windows": windows,
        }
