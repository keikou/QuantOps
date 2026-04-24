from __future__ import annotations

from ai_hedge_bot.alpha_capacity.schemas import CapacityInput


class ImpactModel:
    def estimate(self, item: CapacityInput, liquidity_score: float) -> dict:
        trade_size_fraction = max(0.01, item.weight * item.turnover)
        impact_alpha = 0.7
        impact_cost = (trade_size_fraction / max(liquidity_score, 0.05)) ** impact_alpha * 0.035
        turnover_impact = impact_cost * max(item.turnover, 0.05)
        return {
            "trade_size_fraction": round(trade_size_fraction, 6),
            "impact_cost": round(min(1.0, impact_cost), 6),
            "turnover_impact": round(min(1.0, turnover_impact), 6),
        }

