from __future__ import annotations

from ai_hedge_bot.alpha_capacity.schemas import CapacityInput


class LiquidityModel:
    def score(self, item: CapacityInput) -> dict:
        turnover_penalty = min(item.turnover, 1.0) * 0.28
        concentration_penalty = min(item.max_factor_concentration, 1.5) * 0.12
        liquidity_score = max(0.05, min(1.0, 0.38 + item.capacity_score * 0.58 - turnover_penalty - concentration_penalty))
        spread_penalty = max(0.01, min(0.20, 0.09 - liquidity_score * 0.04 + item.turnover * 0.05))
        volatility_penalty = max(0.02, min(0.25, 0.08 + item.factor_concentration_score * 0.06))
        return {
            "liquidity_score": round(liquidity_score, 6),
            "spread_penalty": round(spread_penalty, 6),
            "volatility_penalty": round(volatility_penalty, 6),
        }

