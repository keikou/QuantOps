from __future__ import annotations

from collections import defaultdict


class FactorExposureEngine:
    def calculate_factor_exposure(self, positions: list[dict], factor_key: str = 'factors') -> dict[str, float]:
        output: dict[str, float] = defaultdict(float)
        for row in positions:
            weight = float(row.get('weight', 0.0))
            for factor_name, loading in (row.get(factor_key) or {}).items():
                output[str(factor_name)] += weight * float(loading)
        return dict(output)
