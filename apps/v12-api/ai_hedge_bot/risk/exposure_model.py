from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(slots=True)
class PositionExposure:
    symbol: str
    weight: float
    abs_weight: float
    side: str
    sector: str | None = None
    strategy_id: str | None = None


class ExposureModel:
    def normalize_positions(self, positions: Iterable[dict[str, Any]]) -> list[PositionExposure]:
        rows: list[PositionExposure] = []
        for row in positions:
            weight = float(row.get('weight', 0.0))
            rows.append(
                PositionExposure(
                    symbol=str(row.get('symbol', 'UNKNOWN')),
                    weight=weight,
                    abs_weight=abs(weight),
                    side=str(row.get('side', 'long')),
                    sector=row.get('sector'),
                    strategy_id=row.get('strategy_id'),
                )
            )
        return rows

    def calculate_gross_exposure(self, positions: Iterable[dict[str, Any]]) -> float:
        return sum(p.abs_weight for p in self.normalize_positions(positions))

    def calculate_net_exposure(self, positions: Iterable[dict[str, Any]]) -> float:
        return sum(p.weight for p in self.normalize_positions(positions))

    def calculate_max_position_weight(self, positions: Iterable[dict[str, Any]]) -> float:
        return max((p.abs_weight for p in self.normalize_positions(positions)), default=0.0)

    def calculate_sector_exposure(self, positions: Iterable[dict[str, Any]]) -> dict[str, float]:
        output: dict[str, float] = defaultdict(float)
        for p in self.normalize_positions(positions):
            output[p.sector or 'unknown'] += p.weight
        return dict(output)

    def calculate_strategy_exposure(self, positions: Iterable[dict[str, Any]]) -> dict[str, float]:
        output: dict[str, float] = defaultdict(float)
        for p in self.normalize_positions(positions):
            output[p.strategy_id or 'default'] += p.weight
        return dict(output)
