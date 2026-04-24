from __future__ import annotations

from math import log, sqrt

from ai_hedge_bot.alpha_evaluation.schemas import AlphaEvaluationCandidate


class OverfitDetector:
    def evaluate(self, candidate: AlphaEvaluationCandidate, sample_count: int, mean_return: float) -> float:
        complexity = log(1 + max(candidate.node_count, 1))
        sample_penalty = 1 / sqrt(max(sample_count, 1))
        performance_gap = abs(mean_return - candidate.execution_cost_adjusted_score)
        score = (0.4 * complexity) + (0.4 * sample_penalty) + (0.2 * performance_gap)
        return round(min(score, 1.5), 6)

