from __future__ import annotations

from ai_hedge_bot.alpha_retirement.schemas import RetirementInput


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


class AlphaHealthEngine:
    def score(self, item: RetirementInput) -> dict:
        negative_weight_pressure = _clamp(abs(min(item.weight_delta, 0.0)) * 10.0)
        deactivation_pressure = _clamp(
            0.45 * (1.0 - item.live_evidence_score)
            + 0.25 * item.crowding_penalty
            + 0.20 * item.impact_penalty
            + 0.10 * negative_weight_pressure
        )
        health_score = _clamp(1.0 - deactivation_pressure)
        if health_score < 0.30:
            health_state = "critical"
        elif health_score < 0.50:
            health_state = "weak"
        elif health_score < 0.70:
            health_state = "watch"
        else:
            health_state = "healthy"
        return {
            "health_score": round(health_score, 6),
            "deactivation_pressure": round(deactivation_pressure, 6),
            "negative_weight_pressure": round(negative_weight_pressure, 6),
            "health_state": health_state,
        }

