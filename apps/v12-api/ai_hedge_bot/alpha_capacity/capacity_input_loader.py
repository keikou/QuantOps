from __future__ import annotations

from ai_hedge_bot.alpha_capacity.schemas import CapacityInput
from ai_hedge_bot.app.container import CONTAINER


class CapacityInputLoader:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def load(self, limit: int = 20) -> list[CapacityInput]:
        weights = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_ensemble_weights
            ORDER BY created_at DESC, ensemble_id ASC, alpha_id ASC
            LIMIT ?
            """,
            [max(int(limit) * 4, 40)],
        )
        residuals = {
            str(row.get("alpha_id") or ""): row
            for row in self.store.fetchall_dict(
                """
                SELECT *
                FROM alpha_residual_alpha_scores
                ORDER BY created_at DESC, alpha_id ASC
                LIMIT 200
                """
            )
        }
        concentration_rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_factor_concentration
            ORDER BY created_at DESC, concentration_score DESC
            LIMIT 100
            """
        )
        concentration_by_ensemble: dict[str, float] = {}
        for row in concentration_rows:
            ensemble_id = str(row.get("ensemble_id") or "")
            score = float(row.get("concentration_score", 0.0) or 0.0)
            concentration_by_ensemble[ensemble_id] = max(concentration_by_ensemble.get(ensemble_id, 0.0), score)

        items: list[CapacityInput] = []
        seen: set[str] = set()
        for row in weights:
            alpha_id = str(row.get("alpha_id") or "")
            if not alpha_id or alpha_id in seen:
                continue
            seen.add(alpha_id)
            ensemble_id = str(row.get("ensemble_id") or "ensemble.synthetic")
            residual = residuals.get(alpha_id, {})
            weight = float(row.get("final_weight", 0.0) or 0.0)
            capacity_score = max(0.05, min(1.0, float(row.get("cap_adjusted_weight", 0.05) or 0.05) * 4.0))
            turnover = max(0.08, min(0.80, 0.24 + weight * 0.35))
            items.append(
                CapacityInput(
                    alpha_id=alpha_id,
                    ensemble_id=ensemble_id,
                    weight=weight,
                    capacity_score=capacity_score,
                    turnover=turnover,
                    residual_alpha_score=float(residual.get("residual_alpha_score", 0.50) or 0.50),
                    factor_concentration_score=concentration_by_ensemble.get(ensemble_id, 0.45),
                    max_factor_concentration=concentration_by_ensemble.get(ensemble_id, 0.45),
                )
            )
            if len(items) >= limit:
                break

        if items:
            return items

        return [
            CapacityInput("alpha.synthetic.capacity.momentum", "ensemble.synthetic", 0.34, 0.58, 0.34, 0.57, 0.52, 0.52),
            CapacityInput("alpha.synthetic.capacity.reversion", "ensemble.synthetic", 0.31, 0.62, 0.27, 0.58, 0.52, 0.52),
            CapacityInput("alpha.synthetic.capacity.quality", "ensemble.synthetic", 0.35, 0.71, 0.18, 0.60, 0.52, 0.52),
        ][:limit]

