from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class RegimeState:
    regime: str
    volatility: float
    correlation: float
    trend_score: float

    def to_dict(self) -> dict:
        return asdict(self)


class RegimeSwitchEngine:
    def detect_regime(self, *, volatility: float, correlation: float, trend_score: float) -> RegimeState:
        if volatility > 0.40 and correlation > 0.70:
            regime = 'crisis'
        elif volatility > 0.25:
            regime = 'volatile'
        elif trend_score > 0.60:
            regime = 'trend'
        else:
            regime = 'mean_reversion'
        return RegimeState(regime=regime, volatility=volatility, correlation=correlation, trend_score=trend_score)
