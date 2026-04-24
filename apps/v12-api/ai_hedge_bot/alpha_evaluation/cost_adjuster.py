from __future__ import annotations

from ai_hedge_bot.alpha_evaluation.schemas import AlphaEvaluationCandidate


class CostAdjuster:
    @staticmethod
    def _turnover_penalty(turnover_profile: str) -> float:
        if turnover_profile in {"high", "rejected"}:
            return 0.18
        if turnover_profile in {"candidate", "shadow"}:
            return 0.11
        return 0.07

    def apply(self, candidate: AlphaEvaluationCandidate, rows: list[dict]) -> tuple[list[dict], float, float]:
        turnover = {"high": 0.78, "candidate": 0.55, "shadow": 0.42}.get(candidate.turnover_profile, 0.31)
        cost_penalty = round(self._turnover_penalty(candidate.turnover_profile), 6)
        adjusted = []
        for row in rows:
            raw = float(row.get("raw_forward_return", 0.0) or 0.0)
            adjusted.append(
                {
                    **row,
                    "cost_adjusted_return": round(raw - cost_penalty, 6),
                }
            )
        return adjusted, turnover, cost_penalty

