from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SelectedAlpha:
    alpha_id: str
    ensemble_id: str
    alpha_family: str
    formula: str
    weight: float
    aes_score: float
    capacity_score: float
    validation_score: float
    regime: str

