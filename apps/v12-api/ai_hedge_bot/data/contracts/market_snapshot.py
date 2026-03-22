from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class MarketSnapshot:
    symbol: str
    timestamp: str
    close: float
    volume: float = 0.0
    funding: float = 0.0
    open_interest: float = 0.0
    liquidation_value: float = 0.0
    orderbook_imbalance: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
