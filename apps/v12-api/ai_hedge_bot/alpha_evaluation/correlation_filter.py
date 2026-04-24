from __future__ import annotations

from ai_hedge_bot.alpha_evaluation.schemas import AlphaEvaluationCandidate


class CorrelationFilter:
    def evaluate(self, candidate: AlphaEvaluationCandidate, peer_count: int) -> dict:
        redundancy = min(
            0.98,
            (candidate.feature_count * 0.08)
            + (candidate.operator_count * 0.05)
            + (max(peer_count - 1, 0) * 0.03),
        )
        return {
            "redundancy_score": round(redundancy, 6),
            "correlation_estimate": round(min(0.99, 0.45 + redundancy), 6),
        }

