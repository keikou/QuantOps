from __future__ import annotations

from ai_hedge_bot.alpha_attribution.schemas import SelectedAlpha
from ai_hedge_bot.app.container import CONTAINER


class AlphaReturnLoader:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def load_selected_alpha(self, limit: int = 20) -> list[SelectedAlpha]:
        selection = self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_ensemble_selection
            WHERE portfolio_ready=true
            ORDER BY created_at DESC
            LIMIT 1
            """
        ) or {}
        if not selection:
            selection = self.store.fetchone_dict(
                """
                SELECT *
                FROM alpha_ensemble_selection
                ORDER BY created_at DESC
                LIMIT 1
                """
            ) or {}
        ensemble_id = str(selection.get("ensemble_id") or "ensemble.synthetic")
        payload = self.store.parse_json(selection.get("payload_json"), {}) or {}
        payload_alphas = list(payload.get("alphas") or [])
        validation_lookup = {
            str(row.get("alpha_id") or ""): row
            for row in self.store.fetchall_dict(
                """
                SELECT *
                FROM alpha_validation_summary
                ORDER BY created_at DESC, alpha_id ASC
                LIMIT 200
                """
            )
        }

        items: list[SelectedAlpha] = []
        for row in payload_alphas[:limit]:
            alpha_id = str(row.get("alpha_id") or "")
            if not alpha_id:
                continue
            weight = float(row.get("weight", 0.0) or 0.0)
            validation = validation_lookup.get(alpha_id, {})
            alpha_family = "momentum" if "momentum" in alpha_id else ("reversion" if "reversion" in alpha_id else "quality")
            regime = "balanced" if alpha_family in {"momentum", "quality"} else "transition"
            items.append(
                SelectedAlpha(
                    alpha_id=alpha_id,
                    ensemble_id=ensemble_id,
                    alpha_family=alpha_family,
                    formula=str(row.get("formula") or f"alpha::{alpha_id}"),
                    weight=weight,
                    aes_score=float(row.get("score", 0.0) or 0.0),
                    capacity_score=float(row.get("capacity_score", 0.0) or 0.0),
                    validation_score=float(validation.get("final_validation_score", 0.55) or 0.55),
                    regime=regime,
                )
            )

        if items:
            return items

        return [
            SelectedAlpha(
                alpha_id="alpha.synthetic.attribution.momentum",
                ensemble_id="ensemble.synthetic",
                alpha_family="momentum",
                formula="rank(momentum_5d - volatility_10d)",
                weight=0.34,
                aes_score=0.66,
                capacity_score=0.58,
                validation_score=0.64,
                regime="balanced",
            ),
            SelectedAlpha(
                alpha_id="alpha.synthetic.attribution.reversion",
                ensemble_id="ensemble.synthetic",
                alpha_family="reversion",
                formula="rank(-returns_3d + volume_impulse_5d)",
                weight=0.31,
                aes_score=0.62,
                capacity_score=0.62,
                validation_score=0.60,
                regime="transition",
            ),
            SelectedAlpha(
                alpha_id="alpha.synthetic.attribution.quality",
                ensemble_id="ensemble.synthetic",
                alpha_family="quality",
                formula="rank(fundamental_quality + cashflow_stability)",
                weight=0.35,
                aes_score=0.64,
                capacity_score=0.71,
                validation_score=0.63,
                regime="balanced",
            ),
        ]

