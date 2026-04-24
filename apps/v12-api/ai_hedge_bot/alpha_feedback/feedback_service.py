from __future__ import annotations

from collections import defaultdict

from ai_hedge_bot.alpha_feedback.feedback_input_loader import FeedbackInputLoader
from ai_hedge_bot.alpha_feedback.motif_engine import MotifEngine
from ai_hedge_bot.alpha_feedback.outcome_engine import OutcomeEngine
from ai_hedge_bot.alpha_feedback.policy_engine import PolicyRecommendationEngine
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id


class AlphaFeedbackService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.loader = FeedbackInputLoader()
        self.outcomes = OutcomeEngine()
        self.motifs = MotifEngine()
        self.policy = PolicyRecommendationEngine()

    def _latest_run(self) -> dict:
        return self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_feedback_runs
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
        rows = self._latest_rows("alpha_realized_outcomes", limit=max(limit * 3, 30))
        items = [
            {
                "alpha_id": row.get("alpha_id"),
                "family_id": row.get("family_id"),
                "outcome_class": row.get("outcome_class"),
                "realized_score": row.get("realized_score"),
                "learning_signal": row.get("learning_signal"),
            }
            for row in rows[:limit]
        ]
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "items": items,
            "alpha_feedback_loop_summary": {
                "alpha_count": run.get("alpha_count"),
                "family_count": run.get("family_count"),
                "recommendation_count": run.get("recommendation_count"),
                "system_alpha_feedback_action": "recommend_bounded_alpha_factory_policy_updates_without_silent_rewrite",
            },
            "as_of": run.get("completed_at"),
        }

    def _materialize_run(self, limit: int = 20) -> dict:
        inputs = self.loader.load(limit=max(limit, 8))
        run_id = new_run_id()
        started_at = utc_now_iso()
        outcome_rows: list[dict] = []
        motif_rows: list[dict] = []
        metric_rows: list[dict] = []
        family_accumulator: dict[str, list[dict]] = defaultdict(list)
        now = utc_now_iso()

        for item in inputs:
            outcome = self.outcomes.classify(item)
            motif = self.motifs.infer(item)
            learning_signal = self._learning_signal(outcome["outcome_class"])
            row = {
                "run_id": run_id,
                "ensemble_id": item.ensemble_id,
                "alpha_id": item.alpha_id,
                "family_id": motif["family_id"],
                "outcome_class": outcome["outcome_class"],
                "realized_score": outcome["realized_score"],
                "learning_signal": learning_signal,
                "created_at": now,
            }
            outcome_rows.append(row)
            family_accumulator[motif["family_id"]].append(row)
            motif_rows.append(
                {
                    "run_id": run_id,
                    "family_id": motif["family_id"],
                    "motif": motif["motif"],
                    "survival_score": outcome["realized_score"],
                    "motif_recommendation": motif["motif_recommendation"],
                    "created_at": now,
                }
            )
            metric_rows.append(
                {
                    "run_id": run_id,
                    "metric_name": "live_evidence_score",
                    "predictiveness_score": round(item.live_evidence_score * outcome["realized_score"], 6),
                    "calibration_action": "raise_threshold" if item.live_evidence_score < 0.55 and outcome["outcome_class"] != "survived_live" else "hold_threshold",
                    "created_at": now,
                }
            )

        family_rows = self._family_rows(run_id, family_accumulator)
        prior_rows = self._prior_rows(run_id, motif_rows)
        aggregate = {
            "degraded_count": sum(1 for row in outcome_rows if row["outcome_class"] in {"failed_live", "unstable_live", "degraded_live"}),
            "crowding_count": sum(1 for row in motif_rows if row["motif_recommendation"] == "reduce_generation_prior"),
        }
        recommendation_rows = [
            {
                "run_id": run_id,
                "policy_area": rec["policy_area"],
                "recommendation": rec["recommendation"],
                "rationale": rec["rationale"],
                "requires_operator_approval": rec["requires_operator_approval"],
                "application_status": "pending_operator_approval" if rec["requires_operator_approval"] else "auto_noop",
                "created_at": utc_now_iso(),
            }
            for rec in self.policy.recommend(aggregate)
        ]

        self.store.append(
            "alpha_feedback_runs",
            {
                "run_id": run_id,
                "started_at": started_at,
                "completed_at": utc_now_iso(),
                "alpha_count": len(outcome_rows),
                "family_count": len(family_rows),
                "recommendation_count": len(recommendation_rows),
                "status": "ok",
                "notes": "aes08_self_improving_alpha_loop",
            },
        )
        for table, rows in [
            ("alpha_realized_outcomes", outcome_rows),
            ("alpha_structural_motifs", motif_rows),
            ("alpha_metric_predictiveness", metric_rows),
            ("alpha_generation_priors", prior_rows),
            ("alpha_family_performance", family_rows),
            ("alpha_policy_recommendations", recommendation_rows),
        ]:
            if rows:
                self.store.append(table, rows)
        return self._build_latest_payload(self._latest_run(), limit=limit)

    def _learning_signal(self, outcome_class: str) -> str:
        return {
            "survived_live": "reinforce_structure",
            "watch_live": "collect_more_evidence",
            "degraded_live": "penalize_or_mutate_structure",
            "unstable_live": "freeze_family_until_review",
            "failed_live": "retire_structure_family_candidate",
        }.get(outcome_class, "collect_more_evidence")

    def _family_rows(self, run_id: str, families: dict[str, list[dict]]) -> list[dict]:
        rows = []
        for family_id, items in families.items():
            avg_score = sum(float(item["realized_score"]) for item in items) / max(len(items), 1)
            degraded_count = sum(1 for item in items if item["outcome_class"] in {"failed_live", "unstable_live", "degraded_live"})
            recommendation = "expand_family" if avg_score >= 0.70 and degraded_count == 0 else "constrain_family" if degraded_count else "watch_family"
            rows.append(
                {
                    "run_id": run_id,
                    "family_id": family_id,
                    "alpha_count": len(items),
                    "average_realized_score": round(avg_score, 6),
                    "degraded_count": degraded_count,
                    "family_recommendation": recommendation,
                    "created_at": utc_now_iso(),
                }
            )
        return rows

    def _prior_rows(self, run_id: str, motif_rows: list[dict]) -> list[dict]:
        rows = []
        for row in motif_rows:
            action = row["motif_recommendation"]
            prior_delta = 0.05 if action == "increase_generation_prior" else -0.05 if action == "reduce_generation_prior" else 0.0
            rows.append(
                {
                    "run_id": run_id,
                    "family_id": row["family_id"],
                    "motif": row["motif"],
                    "prior_delta": prior_delta,
                    "prior_action": action,
                    "created_at": utc_now_iso(),
                }
            )
        return rows

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
        rows = self._latest_rows("alpha_realized_outcomes", limit=max(limit * 3, 30))
        if not rows:
            return self._materialize_run(limit=limit)
        return self._build_latest_payload(run, limit=limit)

    def alpha_learning_signals_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_realized_outcomes", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "alpha_learning_signal_summary": {"signal_count": len(rows[:limit])}}

    def alpha_generation_priors_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_generation_priors", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "alpha_generation_prior_summary": {"prior_update_count": len(rows[:limit])}}

    def alpha_family_performance_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_family_performance", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "alpha_family_performance_summary": {"family_count": len(rows[:limit])}}

    def alpha_policy_recommendations_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("alpha_policy_recommendations", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "alpha_policy_recommendation_summary": {"recommendation_count": len(rows[:limit])}}

    def alpha_feedback_loop_alpha(self, alpha_id: str) -> dict:
        self.latest(limit=20)
        outcome = self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_realized_outcomes
            WHERE alpha_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [alpha_id],
        ) or {}
        motifs = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_structural_motifs
            WHERE family_id=?
            ORDER BY created_at DESC
            LIMIT 20
            """,
            [outcome.get("family_id", "")],
        )
        return {"status": "ok" if outcome else "not_found", "alpha_id": alpha_id, "outcome": outcome, "related_motifs": motifs}

    def alpha_feedback_loop_family(self, family_id: str) -> dict:
        self.latest(limit=20)
        family = self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_family_performance
            WHERE family_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [family_id],
        ) or {}
        priors = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_generation_priors
            WHERE family_id=?
            ORDER BY created_at DESC
            LIMIT 20
            """,
            [family_id],
        )
        return {"status": "ok" if family else "not_found", "family_id": family_id, "family": family, "generation_priors": priors}

    def apply_policy_recommendations(self, recommendation_id: str = "latest", approval: str = "operator_approved") -> dict:
        row = {
            "application_id": new_run_id(),
            "recommendation_id": recommendation_id,
            "approval": approval,
            "application_status": "recorded_for_operator_controlled_application",
            "created_at": utc_now_iso(),
        }
        self.store.append("alpha_policy_applications", row)
        return {"status": "ok", "application": row}

