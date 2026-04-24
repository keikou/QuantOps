from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeedbackInput:
    ensemble_id: str
    alpha_id: str
    lifecycle_state: str
    decision: str
    decision_reason: str
    health_score: float
    deactivation_pressure: float
    live_evidence_score: float
    crowding_penalty: float
    impact_penalty: float

