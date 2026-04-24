from __future__ import annotations

from ai_hedge_bot.alpha_capacity.capacity_service import AlphaCapacityService
from ai_hedge_bot.alpha_weighting.schemas import WeightingInput
from ai_hedge_bot.app.container import CONTAINER


class WeightingInputLoader:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.capacity = AlphaCapacityService()

    def _latest_capacity_run_id(self) -> str:
        row = self.store.fetchone_dict(
            """
            SELECT run_id
            FROM alpha_capacity_runs
            ORDER BY completed_at DESC, started_at DESC
            LIMIT 1
            """
        ) or {}
        return str(row.get("run_id") or "")

    def load(self, limit: int = 20) -> list[WeightingInput]:
        run_id = self._latest_capacity_run_id()
        if not run_id:
            self.capacity.run(limit=limit)
            run_id = self._latest_capacity_run_id()

        rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_capacity
            WHERE run_id=?
            ORDER BY ensemble_id ASC, capacity DESC, alpha_id ASC
            LIMIT ?
            """,
            [run_id, max(int(limit), 1)],
        )
        if not rows:
            self.capacity.run(limit=limit)
            run_id = self._latest_capacity_run_id()
            rows = self.store.fetchall_dict(
                """
                SELECT *
                FROM alpha_capacity
                WHERE run_id=?
                ORDER BY ensemble_id ASC, capacity DESC, alpha_id ASC
                LIMIT ?
                """,
                [run_id, max(int(limit), 1)],
            )

        return [
            WeightingInput(
                ensemble_id=str(row.get("ensemble_id") or "ensemble.1"),
                alpha_id=str(row.get("alpha_id") or ""),
                current_weight=float(row.get("weight") or 0.0),
                liquidity_score=float(row.get("liquidity_score") or 0.0),
                turnover=float(row.get("turnover") or 0.0),
                impact_cost=float(row.get("impact_cost") or 0.0),
                capacity=float(row.get("capacity") or 0.0),
                crowding_score=float(row.get("crowding_score") or 0.0),
                impact_adjusted_return=float(row.get("impact_adjusted_return") or 0.0),
                scaling_recommendation=str(row.get("scaling_recommendation") or "unknown"),
            )
            for row in rows
        ]

