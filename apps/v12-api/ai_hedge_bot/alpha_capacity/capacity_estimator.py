from __future__ import annotations

from ai_hedge_bot.alpha_capacity.schemas import CapacityInput


class CapacityEstimator:
    def estimate(self, item: CapacityInput, liquidity: dict, impact: dict, crowding: dict) -> dict:
        liquidity_score = float(liquidity.get("liquidity_score", 0.0) or 0.0)
        crowding_score = float(crowding.get("crowding_score", 0.0) or 0.0)
        impact_cost = float(impact.get("impact_cost", 0.0) or 0.0)
        raw_capacity = liquidity_score * (1.0 / max(item.turnover, 0.05)) * 0.05
        adjusted_capacity = raw_capacity * (1.0 - min(crowding_score, 0.95)) * max(item.residual_alpha_score, 0.05)
        impact_adjusted_return = max(0.0, item.residual_alpha_score * 0.08 - impact_cost)
        if crowding_score > 0.80 or impact_adjusted_return <= 0.0:
            recommendation = "do_not_scale"
        elif adjusted_capacity < 0.025:
            recommendation = "scale_limited"
        elif liquidity_score >= 0.60 and crowding_score < 0.50:
            recommendation = "scale_full"
        else:
            recommendation = "scale_partial"
        return {
            "impact_adjusted_return": round(impact_adjusted_return, 6),
            "capacity": round(max(0.0, adjusted_capacity), 6),
            "scaling_recommendation": recommendation,
        }

