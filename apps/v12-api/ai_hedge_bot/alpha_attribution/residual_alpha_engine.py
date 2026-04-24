from __future__ import annotations

from ai_hedge_bot.alpha_attribution.schemas import SelectedAlpha


class ResidualAlphaEngine:
    def score(self, alpha: SelectedAlpha, exposures: list[dict]) -> dict:
        explained = min(0.95, sum(float(row.get("exposure_strength", 0.0) or 0.0) for row in exposures) / max(len(exposures), 1))
        residual_sharpe = max(0.0, 0.35 + (alpha.validation_score * 0.45) + (alpha.capacity_score * 0.20) - (explained * 0.35))
        residual_hit_rate = max(0.0, min(1.0, 0.48 + alpha.validation_score * 0.25 - explained * 0.10))
        residual_mean_return = max(0.0, 0.006 + alpha.aes_score * 0.015 - explained * 0.004)
        residual_volatility = max(0.02, 0.18 + explained * 0.12)
        residual_alpha_score = (
            (0.45 * min(residual_sharpe, 1.0))
            + (0.25 * residual_hit_rate)
            + (0.20 * min(residual_mean_return * 20.0, 1.0))
            + (0.10 * (1.0 - explained))
        )
        quality = "strong_residual_alpha" if residual_alpha_score >= 0.70 and explained <= 0.50 else (
            "moderate_residual_alpha" if residual_alpha_score >= 0.50 else (
                "factor_explained_alpha" if explained > 0.70 else "weak_residual_alpha"
            )
        )
        return {
            "raw_alpha_score": round(alpha.aes_score, 6),
            "factor_explained_score": round(explained, 6),
            "residual_alpha_score": round(max(0.0, min(1.0, residual_alpha_score)), 6),
            "residual_sharpe": round(residual_sharpe, 6),
            "residual_hit_rate": round(residual_hit_rate, 6),
            "residual_mean_return": round(residual_mean_return, 6),
            "residual_volatility": round(residual_volatility, 6),
            "residual_quality": quality,
        }

