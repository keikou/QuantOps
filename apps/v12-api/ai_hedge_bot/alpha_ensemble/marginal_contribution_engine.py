from __future__ import annotations

from ai_hedge_bot.alpha_ensemble.schemas import ValidatedAlpha


class MarginalContributionEngine:
    def compute(self, ensemble_alpha_ids: list[str], alpha_by_id: dict[str, ValidatedAlpha], correlations: list[dict]) -> list[dict]:
        corr_lookup: dict[tuple[str, str], float] = {}
        for row in correlations:
            key = tuple(sorted([str(row.get("alpha_id_a") or ""), str(row.get("alpha_id_b") or "")]))
            corr_lookup[key] = float(row.get("correlation", 0.0) or 0.0)

        items: list[dict] = []
        for alpha_id in ensemble_alpha_ids:
            alpha = alpha_by_id[alpha_id]
            peers = [peer_id for peer_id in ensemble_alpha_ids if peer_id != alpha_id]
            avg_corr = (
                sum(corr_lookup.get(tuple(sorted([alpha_id, peer_id])), 0.0) for peer_id in peers) / len(peers)
                if peers
                else 0.0
            )
            contribution_to_return = max(0.0, alpha.validation_score * 0.55 + alpha.aes_score * 0.45)
            contribution_to_risk = max(0.0, min(1.0, alpha.overfit_risk * 0.6 + alpha.turnover * 0.3 + avg_corr * 0.4))
            contribution_to_sharpe = max(0.0, min(1.0, alpha.sharpe_final / 2.5))
            contribution_to_diversification = max(0.0, min(1.0, 1.0 - avg_corr))
            marginal_score = max(
                0.0,
                min(
                    1.0,
                    (0.40 * contribution_to_return)
                    + (0.25 * contribution_to_sharpe)
                    + (0.20 * contribution_to_diversification)
                    + (0.15 * alpha.capacity_score)
                    - (0.20 * contribution_to_risk),
                ),
            )
            items.append(
                {
                    "alpha_id": alpha_id,
                    "contribution_to_return": round(contribution_to_return, 6),
                    "contribution_to_risk": round(contribution_to_risk, 6),
                    "contribution_to_sharpe": round(contribution_to_sharpe, 6),
                    "contribution_to_diversification": round(contribution_to_diversification, 6),
                    "marginal_score": round(marginal_score, 6),
                }
            )
        return items

