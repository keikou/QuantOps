from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ValidatedAlpha:
    alpha_id: str
    alpha_family: str
    regime: str
    source: str
    formula: str
    aes_score: float
    validation_score: float
    robustness_score: float
    decay_score: float
    overfit_risk: float
    mean_return: float
    sharpe_final: float
    capacity_score: float
    turnover: float
    decision: str


@dataclass(slots=True)
class EnsembleCandidate:
    ensemble_id: str
    alpha_ids: list[str]
    source: str

