from __future__ import annotations


class FactorDataLoader:
    def load_factor_set(self) -> list[dict]:
        return [
            {"factor_name": "market_beta", "factor_group": "market"},
            {"factor_name": "momentum", "factor_group": "style"},
            {"factor_name": "value_quality", "factor_group": "style"},
            {"factor_name": "volatility", "factor_group": "risk"},
            {"factor_name": "liquidity", "factor_group": "microstructure"},
        ]

