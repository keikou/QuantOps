from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetirementInput:
    ensemble_id: str
    alpha_id: str
    current_weight: float
    final_weight: float
    weight_delta: float
    weight_change_reason: str
    constraint_action: str
    live_evidence_score: float
    crowding_penalty: float
    impact_penalty: float

