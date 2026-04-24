from __future__ import annotations

from ai_hedge_bot.alpha_feedback.schemas import FeedbackInput
from ai_hedge_bot.alpha_retirement.retirement_service import AlphaRetirementService
from ai_hedge_bot.app.container import CONTAINER


class FeedbackInputLoader:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.retirement = AlphaRetirementService()

    def _latest_retirement_run_id(self) -> str:
        row = self.store.fetchone_dict(
            """
            SELECT run_id
            FROM alpha_retirement_runs
            ORDER BY completed_at DESC, started_at DESC
            LIMIT 1
            """
        ) or {}
        return str(row.get("run_id") or "")

    def load(self, limit: int = 20) -> list[FeedbackInput]:
        run_id = self._latest_retirement_run_id()
        if not run_id:
            self.retirement.run(limit=limit)
            run_id = self._latest_retirement_run_id()

        rows = self.store.fetchall_dict(
            """
            SELECT
                d.ensemble_id,
                d.alpha_id,
                d.lifecycle_state,
                d.decision,
                d.decision_reason,
                COALESCE(h.health_score, 0.5) AS health_score,
                COALESCE(h.deactivation_pressure, 0.5) AS deactivation_pressure,
                COALESCE(h.live_evidence_score, 0.5) AS live_evidence_score,
                COALESCE(h.crowding_penalty, 0.0) AS crowding_penalty,
                COALESCE(h.impact_penalty, 0.0) AS impact_penalty
            FROM alpha_retirement_decisions d
            LEFT JOIN alpha_live_health h
              ON h.run_id=d.run_id AND h.alpha_id=d.alpha_id
            WHERE d.run_id=?
            ORDER BY h.health_score ASC, d.alpha_id ASC
            LIMIT ?
            """,
            [run_id, max(int(limit), 1)],
        )
        if not rows:
            self.retirement.run(limit=limit)
            run_id = self._latest_retirement_run_id()
            rows = self.store.fetchall_dict(
                """
                SELECT
                    d.ensemble_id,
                    d.alpha_id,
                    d.lifecycle_state,
                    d.decision,
                    d.decision_reason,
                    COALESCE(h.health_score, 0.5) AS health_score,
                    COALESCE(h.deactivation_pressure, 0.5) AS deactivation_pressure,
                    COALESCE(h.live_evidence_score, 0.5) AS live_evidence_score,
                    COALESCE(h.crowding_penalty, 0.0) AS crowding_penalty,
                    COALESCE(h.impact_penalty, 0.0) AS impact_penalty
                FROM alpha_retirement_decisions d
                LEFT JOIN alpha_live_health h
                  ON h.run_id=d.run_id AND h.alpha_id=d.alpha_id
                WHERE d.run_id=?
                ORDER BY h.health_score ASC, d.alpha_id ASC
                LIMIT ?
                """,
                [run_id, max(int(limit), 1)],
            )

        return [
            FeedbackInput(
                ensemble_id=str(row.get("ensemble_id") or "ensemble.1"),
                alpha_id=str(row.get("alpha_id") or ""),
                lifecycle_state=str(row.get("lifecycle_state") or "active"),
                decision=str(row.get("decision") or "continue_alpha"),
                decision_reason=str(row.get("decision_reason") or "unknown"),
                health_score=float(row.get("health_score") or 0.0),
                deactivation_pressure=float(row.get("deactivation_pressure") or 0.0),
                live_evidence_score=float(row.get("live_evidence_score") or 0.0),
                crowding_penalty=float(row.get("crowding_penalty") or 0.0),
                impact_penalty=float(row.get("impact_penalty") or 0.0),
            )
            for row in rows
        ]

