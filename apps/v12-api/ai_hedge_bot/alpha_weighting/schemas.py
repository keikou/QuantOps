from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WeightingInput:
    ensemble_id: str
    alpha_id: str
    current_weight: float
    liquidity_score: float
    turnover: float
    impact_cost: float
    capacity: float
    crowding_score: float
    impact_adjusted_return: float
    scaling_recommendation: str

