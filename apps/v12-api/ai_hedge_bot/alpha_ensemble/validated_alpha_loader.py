from __future__ import annotations

from ai_hedge_bot.alpha_ensemble.schemas import ValidatedAlpha
from ai_hedge_bot.app.container import CONTAINER


class ValidatedAlphaLoader:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    @staticmethod
    def _fallback_pool() -> list[ValidatedAlpha]:
        return [
            ValidatedAlpha(
                alpha_id="alpha.synthetic.ensemble.momentum",
                alpha_family="momentum",
                regime="balanced",
                source="aes02_fallback",
                formula="rank(momentum_5d - volatility_10d)",
                aes_score=0.66,
                validation_score=0.64,
                robustness_score=0.61,
                decay_score=0.79,
                overfit_risk=0.22,
                mean_return=0.018,
                sharpe_final=0.72,
                capacity_score=0.58,
                turnover=0.34,
                decision="validation_watchlist",
            ),
            ValidatedAlpha(
                alpha_id="alpha.synthetic.ensemble.reversion",
                alpha_family="reversion",
                regime="transition",
                source="aes02_fallback",
                formula="rank(-returns_3d + volume_impulse_5d)",
                aes_score=0.62,
                validation_score=0.60,
                robustness_score=0.59,
                decay_score=0.83,
                overfit_risk=0.18,
                mean_return=0.015,
                sharpe_final=0.68,
                capacity_score=0.62,
                turnover=0.27,
                decision="validation_watchlist",
            ),
            ValidatedAlpha(
                alpha_id="alpha.synthetic.ensemble.quality",
                alpha_family="quality",
                regime="balanced",
                source="aes02_fallback",
                formula="rank(fundamental_quality + cashflow_stability)",
                aes_score=0.64,
                validation_score=0.63,
                robustness_score=0.66,
                decay_score=0.88,
                overfit_risk=0.14,
                mean_return=0.017,
                sharpe_final=0.74,
                capacity_score=0.71,
                turnover=0.18,
                decision="validation_pass",
            ),
        ]

    def load_validated_alphas(self, limit: int = 20) -> list[ValidatedAlpha]:
        rows = self.store.fetchall_dict(
            """
            SELECT
                v.alpha_id,
                v.final_validation_score,
                v.decision AS validation_decision,
                v.reason,
                e.final_score,
                e.robustness_score,
                e.decay_score,
                e.overfit_risk,
                e.mean_return,
                e.sharpe_final,
                e.turnover,
                e.details_json
            FROM alpha_validation_summary v
            LEFT JOIN alpha_evaluation_scores e
                ON e.alpha_id = v.alpha_id
            WHERE v.decision IN ('validation_pass', 'validation_watchlist')
            ORDER BY
                CASE WHEN v.decision = 'validation_pass' THEN 0 ELSE 1 END,
                v.final_validation_score DESC,
                e.final_score DESC,
                v.alpha_id ASC
            LIMIT ?
            """,
            [max(int(limit), 1) * 3],
        )

        if not rows:
            return self._fallback_pool()[:limit]

        items: list[ValidatedAlpha] = []
        seen: set[str] = set()
        for row in rows:
            alpha_id = str(row.get("alpha_id") or "")
            if not alpha_id or alpha_id in seen:
                continue
            seen.add(alpha_id)
            details = self.store.parse_json(row.get("details_json"), {}) or {}
            alpha_family = str(details.get("alpha_family") or "unknown")
            items.append(
                ValidatedAlpha(
                    alpha_id=alpha_id,
                    alpha_family=alpha_family,
                    regime="balanced" if alpha_family in {"momentum", "trend"} else "transition",
                    source="aes02_validated_pool",
                    formula=str(details.get("formula") or f"alpha::{alpha_id}"),
                    aes_score=float(row.get("final_score", 0.0) or 0.0),
                    validation_score=float(row.get("final_validation_score", 0.0) or 0.0),
                    robustness_score=float(row.get("robustness_score", 0.0) or 0.0),
                    decay_score=float(row.get("decay_score", 0.0) or 0.0),
                    overfit_risk=float(row.get("overfit_risk", 0.0) or 0.0),
                    mean_return=float(row.get("mean_return", 0.0) or 0.0),
                    sharpe_final=float(row.get("sharpe_final", 0.0) or 0.0),
                    capacity_score=max(0.05, min(1.0, 0.55 + float(row.get("robustness_score", 0.0) or 0.0) * 0.35)),
                    turnover=float(row.get("turnover", 0.0) or 0.0),
                    decision=str(row.get("validation_decision") or "validation_watchlist"),
                )
            )
            if len(items) >= limit:
                break
        if len(items) < 2:
            existing = {item.alpha_id for item in items}
            for alpha in self._fallback_pool():
                if alpha.alpha_id in existing:
                    continue
                items.append(alpha)
                if len(items) >= limit or len(items) >= 3:
                    break
        return items
