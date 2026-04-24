from __future__ import annotations

from statistics import mean

from ai_hedge_bot.alpha_evaluation.schemas import AlphaEvaluationCandidate


class ForwardReturnEngine:
    HORIZONS = ("1d", "5d", "20d")

    @staticmethod
    def _profile_scale(turnover_profile: str) -> float:
        if turnover_profile in {"rejected", "high"}:
            return 0.85
        if turnover_profile in {"shadow", "candidate"}:
            return 0.95
        return 1.0

    def compute(self, candidate: AlphaEvaluationCandidate) -> list[dict]:
        base = (
            (candidate.rank_score * 0.45)
            + (candidate.expected_return * 0.35)
            + (candidate.execution_cost_adjusted_score * 0.20)
        )
        scale = self._profile_scale(candidate.turnover_profile)
        rows = []
        for idx, horizon in enumerate(self.HORIZONS, start=1):
            raw = round((base * scale) - (0.012 * idx) + (candidate.diversification_value * 0.03), 6)
            rows.append(
                {
                    "alpha_id": candidate.alpha_id,
                    "horizon": horizon,
                    "raw_forward_return": raw,
                }
            )
        return rows

    @staticmethod
    def mean_raw(rows: list[dict]) -> float:
        if not rows:
            return 0.0
        return float(mean(float(row.get("raw_forward_return", 0.0) or 0.0) for row in rows))

