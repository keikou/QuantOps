from __future__ import annotations

from ai_hedge_bot.alpha_retirement.schemas import RetirementInput
from ai_hedge_bot.alpha_weighting.weighting_service import AlphaWeightingService
from ai_hedge_bot.app.container import CONTAINER


class RetirementInputLoader:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.weighting = AlphaWeightingService()

    def _latest_weighting_run_id(self) -> str:
        row = self.store.fetchone_dict(
            """
            SELECT run_id
            FROM alpha_weighting_runs
            ORDER BY completed_at DESC, started_at DESC
            LIMIT 1
            """
        ) or {}
        return str(row.get("run_id") or "")

    def load(self, limit: int = 20) -> list[RetirementInput]:
        run_id = self._latest_weighting_run_id()
        if not run_id:
            self.weighting.run(limit=limit)
            run_id = self._latest_weighting_run_id()

        rows = self.store.fetchall_dict(
            """
            SELECT
                w.ensemble_id,
                w.alpha_id,
                w.current_weight,
                w.final_weight,
                w.weight_delta,
                w.weight_change_reason,
                w.constraint_action,
                COALESCE(s.live_evidence_score, 0.5) AS live_evidence_score,
                COALESCE(s.crowding_penalty, 0.0) AS crowding_penalty,
                COALESCE(s.impact_penalty, 0.0) AS impact_penalty
            FROM alpha_dynamic_weights w
            LEFT JOIN alpha_live_state s
              ON s.run_id=w.run_id AND s.alpha_id=w.alpha_id
            WHERE w.run_id=?
            ORDER BY w.final_weight ASC, w.alpha_id ASC
            LIMIT ?
            """,
            [run_id, max(int(limit), 1)],
        )
        if not rows:
            self.weighting.run(limit=limit)
            run_id = self._latest_weighting_run_id()
            rows = self.store.fetchall_dict(
                """
                SELECT
                    w.ensemble_id,
                    w.alpha_id,
                    w.current_weight,
                    w.final_weight,
                    w.weight_delta,
                    w.weight_change_reason,
                    w.constraint_action,
                    COALESCE(s.live_evidence_score, 0.5) AS live_evidence_score,
                    COALESCE(s.crowding_penalty, 0.0) AS crowding_penalty,
                    COALESCE(s.impact_penalty, 0.0) AS impact_penalty
                FROM alpha_dynamic_weights w
                LEFT JOIN alpha_live_state s
                  ON s.run_id=w.run_id AND s.alpha_id=w.alpha_id
                WHERE w.run_id=?
                ORDER BY w.final_weight ASC, w.alpha_id ASC
                LIMIT ?
                """,
                [run_id, max(int(limit), 1)],
            )

        return [
            RetirementInput(
                ensemble_id=str(row.get("ensemble_id") or "ensemble.1"),
                alpha_id=str(row.get("alpha_id") or ""),
                current_weight=float(row.get("current_weight") or 0.0),
                final_weight=float(row.get("final_weight") or 0.0),
                weight_delta=float(row.get("weight_delta") or 0.0),
                weight_change_reason=str(row.get("weight_change_reason") or "unknown"),
                constraint_action=str(row.get("constraint_action") or "unknown"),
                live_evidence_score=float(row.get("live_evidence_score") or 0.0),
                crowding_penalty=float(row.get("crowding_penalty") or 0.0),
                impact_penalty=float(row.get("impact_penalty") or 0.0),
            )
            for row in rows
        ]

