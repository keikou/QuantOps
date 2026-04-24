from __future__ import annotations


class FactorConcentrationEngine:
    def compute(self, ensemble_id: str, weighted_exposures: dict[str, float]) -> list[dict]:
        max_allowed = {
            "market_beta": 0.50,
            "momentum": 0.40,
            "value_quality": 0.40,
            "volatility": 0.35,
            "liquidity": 0.35,
        }
        items = []
        for factor_name, weighted_exposure in weighted_exposures.items():
            absolute = abs(weighted_exposure)
            limit = max_allowed.get(factor_name, 0.40)
            concentration_score = absolute / limit if limit > 0 else 0.0
            items.append(
                {
                    "ensemble_id": ensemble_id,
                    "factor_name": factor_name,
                    "weighted_exposure": round(weighted_exposure, 6),
                    "absolute_weighted_exposure": round(absolute, 6),
                    "concentration_score": round(concentration_score, 6),
                    "concentration_flag": concentration_score > 1.0,
                }
            )
        return items

