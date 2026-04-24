from __future__ import annotations

from ai_hedge_bot.alpha_attribution.schemas import SelectedAlpha


class ExposureEstimator:
    def estimate(self, alpha: SelectedAlpha, factors: list[dict]) -> list[dict]:
        rows: list[dict] = []
        family_bias = {
            "momentum": {"market_beta": 0.28, "momentum": 0.56, "volatility": 0.22, "liquidity": 0.14, "value_quality": 0.18},
            "reversion": {"market_beta": 0.12, "momentum": -0.18, "volatility": 0.31, "liquidity": 0.24, "value_quality": 0.20},
            "quality": {"market_beta": 0.19, "momentum": 0.14, "volatility": 0.11, "liquidity": 0.10, "value_quality": 0.52},
        }.get(alpha.alpha_family, {})
        for factor in factors:
            factor_name = str(factor.get("factor_name") or "")
            beta = float(family_bias.get(factor_name, 0.10))
            if alpha.regime == "transition" and factor_name in {"volatility", "liquidity"}:
                beta += 0.08
            t_stat = abs(beta) * 4.0
            p_value = 0.03 if abs(beta) >= 0.20 else 0.08
            strength = abs(beta) * (1.0 if p_value < 0.05 else 0.5)
            rows.append(
                {
                    "factor_name": factor_name,
                    "factor_group": factor.get("factor_group"),
                    "beta": round(beta, 6),
                    "t_stat": round(t_stat, 6),
                    "p_value": round(p_value, 6),
                    "exposure_strength": round(strength, 6),
                    "exposure_direction": "positive" if beta > 0.02 else ("negative" if beta < -0.02 else "neutral"),
                    "significant": p_value < 0.10,
                }
            )
        return rows

