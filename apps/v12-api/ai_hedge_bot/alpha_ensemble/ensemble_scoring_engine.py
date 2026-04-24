from __future__ import annotations

from ai_hedge_bot.alpha_ensemble.schemas import ValidatedAlpha


class EnsembleScoringEngine:
    def score(
        self,
        ensemble_alpha_ids: list[str],
        alpha_by_id: dict[str, ValidatedAlpha],
        diversification: dict,
        marginal_rows: list[dict],
    ) -> dict:
        alphas = [alpha_by_id[alpha_id] for alpha_id in ensemble_alpha_ids]
        expected_return_score = sum(max(0.0, alpha.mean_return) for alpha in alphas) / max(len(alphas), 1)
        expected_return_score = max(0.0, min(1.0, expected_return_score * 20.0))
        expected_risk_score = max(
            0.0,
            min(1.0, sum((alpha.overfit_risk * 0.5) + (alpha.turnover * 0.25) for alpha in alphas) / max(len(alphas), 1)),
        )
        sharpe_score = max(0.0, min(1.0, sum(alpha.sharpe_final for alpha in alphas) / max(len(alphas), 1) / 2.0))
        stability_score = max(0.0, min(1.0, sum(alpha.validation_score for alpha in alphas) / max(len(alphas), 1)))
        capacity_score = max(0.0, min(1.0, sum(alpha.capacity_score for alpha in alphas) / max(len(alphas), 1)))
        marginal_score = sum(float(row.get("marginal_score", 0.0) or 0.0) for row in marginal_rows) / max(len(marginal_rows), 1)
        final_score = (
            (0.35 * sharpe_score)
            + (0.25 * float(diversification.get("diversification_score", 0.0) or 0.0))
            + (0.20 * stability_score)
            + (0.15 * capacity_score)
            + (0.05 * marginal_score)
            - (0.05 * float(diversification.get("concentration_penalty", 0.0) or 0.0))
        )
        return {
            "expected_return_score": round(expected_return_score, 6),
            "expected_risk_score": round(expected_risk_score, 6),
            "sharpe_score": round(sharpe_score, 6),
            "diversification_score": round(float(diversification.get("diversification_score", 0.0) or 0.0), 6),
            "stability_score": round(stability_score, 6),
            "capacity_score": round(capacity_score, 6),
            "concentration_penalty": round(float(diversification.get("concentration_penalty", 0.0) or 0.0), 6),
            "final_ensemble_score": round(max(0.0, min(1.0, final_score)), 6),
        }

