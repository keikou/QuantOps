from __future__ import annotations

from ai_hedge_bot.alpha_ensemble.schemas import ValidatedAlpha


class DiversificationScorer:
    def score(self, ensemble_alpha_ids: list[str], alpha_by_id: dict[str, ValidatedAlpha], correlations: list[dict]) -> dict:
        corr_values = []
        families: dict[str, int] = {}
        regimes: dict[str, int] = {}
        for row in correlations:
            corr_values.append(float(row.get("correlation", 0.0) or 0.0))
        for alpha_id in ensemble_alpha_ids:
            alpha = alpha_by_id[alpha_id]
            families[alpha.alpha_family] = families.get(alpha.alpha_family, 0) + 1
            regimes[alpha.regime] = regimes.get(alpha.regime, 0) + 1

        avg_corr = sum(corr_values) / len(corr_values) if corr_values else 0.0
        max_corr = max(corr_values) if corr_values else 0.0
        family_concentration = max(families.values()) / max(len(ensemble_alpha_ids), 1)
        regime_concentration = max(regimes.values()) / max(len(ensemble_alpha_ids), 1)
        concentration_penalty = max(0.0, min(1.0, (family_concentration * 0.6) + (regime_concentration * 0.4) - 0.5))
        diversification_score = max(0.0, min(1.0, 1.0 - ((avg_corr * 0.55) + (max_corr * 0.25) + (concentration_penalty * 0.20))))
        return {
            "avg_corr": round(avg_corr, 6),
            "max_corr": round(max_corr, 6),
            "family_concentration": round(family_concentration, 6),
            "regime_concentration": round(regime_concentration, 6),
            "concentration_penalty": round(concentration_penalty, 6),
            "diversification_score": round(diversification_score, 6),
        }

