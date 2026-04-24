from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AlphaEvaluationCandidate:
    alpha_id: str
    alpha_family: str
    source: str
    rank_score: float
    expected_return: float
    execution_cost_adjusted_score: float
    diversification_value: float
    turnover_profile: str
    node_count: int
    feature_count: int
    operator_count: int
    formula: str

