from __future__ import annotations

from ai_hedge_bot.alpha_weighting.schemas import WeightingInput


class SmoothingEngine:
    def __init__(self, smoothing_lambda: float = 0.35) -> None:
        self.smoothing_lambda = smoothing_lambda

    def smooth(self, item: WeightingInput, target_weight: float) -> float:
        prior = item.current_weight
        return round((1.0 - self.smoothing_lambda) * prior + self.smoothing_lambda * target_weight, 6)

