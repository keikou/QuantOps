from __future__ import annotations

from ai_hedge_bot.alpha_weighting.schemas import WeightingInput


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


class LiveStateModel:
    def score(self, item: WeightingInput) -> dict:
        return_signal = _clamp(0.50 + item.impact_adjusted_return * 5.0)
        capacity_signal = _clamp(item.capacity * 25.0)
        liquidity_signal = _clamp(item.liquidity_score)
        crowding_penalty = _clamp(item.crowding_score)
        impact_penalty = _clamp(item.impact_cost * 8.0)
        live_evidence_score = _clamp(
            0.35 * return_signal
            + 0.25 * capacity_signal
            + 0.20 * liquidity_signal
            + 0.20 * (1.0 - max(crowding_penalty, impact_penalty))
        )
        return {
            "return_signal": round(return_signal, 6),
            "capacity_signal": round(capacity_signal, 6),
            "liquidity_signal": round(liquidity_signal, 6),
            "crowding_penalty": round(crowding_penalty, 6),
            "impact_penalty": round(impact_penalty, 6),
            "live_evidence_score": round(live_evidence_score, 6),
        }

