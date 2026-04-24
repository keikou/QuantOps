from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CapacityInput:
    alpha_id: str
    ensemble_id: str
    weight: float
    capacity_score: float
    turnover: float
    residual_alpha_score: float
    factor_concentration_score: float
    max_factor_concentration: float

