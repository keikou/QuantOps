from __future__ import annotations

from ai_hedge_bot.core.settings import SETTINGS
from ai_hedge_bot.core.types import ExpectedReturnEstimate


class PortfolioOptimizer:
    def optimize(self, estimates: list[ExpectedReturnEstimate], max_gross: float, max_symbol_weight: float) -> dict[str, float]:
        if not estimates:
            return {}
        raw_weights: dict[str, float] = {}
        for estimate in estimates:
            utility = max(0.0, estimate.expected_return_net - SETTINGS.risk_aversion * (estimate.expected_volatility ** 2))
            raw_weights[estimate.signal_id] = max(0.0, utility)
        total = sum(raw_weights.values())
        if total <= 0:
            equal = min(max_symbol_weight, max_gross / len(estimates))
            return {estimate.signal_id: round(equal, 6) for estimate in estimates}
        scaled = {signal_id: min(max_symbol_weight, max_gross * weight / total) for signal_id, weight in raw_weights.items()}
        gross = sum(scaled.values())
        if gross > max_gross and gross > 0:
            factor = max_gross / gross
            scaled = {k: round(v * factor, 6) for k, v in scaled.items()}
        return {k: round(v, 6) for k, v in scaled.items()}
