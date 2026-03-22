from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from ai_hedge_bot.core.enums import Side, Regime


@dataclass
class SignalCandidate:
    signal_id: str
    symbol: str
    side: Side
    score: float
    dominant_alpha: str
    alpha_family: str
    horizon: str
    turnover_profile: str
    regime: Regime = Regime.NEUTRAL
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PositionIntent:
    symbol: str
    side: Side
    target_weight: float
    reason: str


@dataclass
class OrderIntent:
    symbol: str
    side: Side
    quantity: float
    order_type: str = 'market'
