from __future__ import annotations

from ai_hedge_bot.core.settings import SETTINGS


class ExecutionCostModel:
    def signed_slippage_bps(self, side: str, arrival_mid_price: float, fill_price: float) -> float:
        if arrival_mid_price <= 0:
            return 0.0
        sign = 1.0 if side == 'long' else -1.0
        return sign * (fill_price - arrival_mid_price) / arrival_mid_price * 10000.0

    def build(self, side: str, arrival_mid_price: float, fill_price: float, impact_cost_bps: float, latency_cost_bps: float, fee_bps: float) -> dict:
        slippage_bps = self.signed_slippage_bps(side, arrival_mid_price, fill_price)
        spread_cost_bps = SETTINGS.shadow_spread_bps
        total = spread_cost_bps + slippage_bps + impact_cost_bps + latency_cost_bps + fee_bps
        return {
            'spread_cost_bps': round(spread_cost_bps, 6),
            'slippage_bps': round(slippage_bps, 6),
            'latency_cost_bps': round(latency_cost_bps, 6),
            'impact_cost_bps': round(impact_cost_bps, 6),
            'fee_bps': round(fee_bps, 6),
            'total_cost_bps': round(total, 6),
        }
