from __future__ import annotations

from ai_hedge_bot.core.types import ExpectedReturnEstimate


class RiskModel:
    def marginal_risk(self, estimate: ExpectedReturnEstimate) -> float:
        directional_multiplier = 1.0 if estimate.side == 'long' else 1.05
        return round(max(0.0001, estimate.expected_volatility * directional_multiplier), 6)
