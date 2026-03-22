from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class AlphaMetricsSnapshot:
    run_id: str
    created_at: str
    information_coefficient: float
    ic_decay_1: float
    signal_turnover: float
    candidate_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AlphaMetricsEngine:
    def calculate_ic(self, signal_values: list[float], forward_returns: list[float]) -> float:
        if not signal_values or len(signal_values) != len(forward_returns) or len(signal_values) <= 1:
            return 0.0
        n = len(signal_values)
        mean_x = sum(signal_values) / n
        mean_y = sum(forward_returns) / n
        cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(signal_values, forward_returns))
        var_x = sum((x - mean_x) ** 2 for x in signal_values)
        var_y = sum((y - mean_y) ** 2 for y in forward_returns)
        if var_x == 0 or var_y == 0:
            return 0.0
        return cov / (var_x * var_y) ** 0.5

    def calculate_ic_decay(self, ic_series: list[float], lag: int = 1) -> float:
        if len(ic_series) <= lag:
            return 0.0
        return ic_series[-lag - 1] - ic_series[-1]

    def calculate_signal_turnover(self, previous_signals: dict[str, float], current_signals: dict[str, float]) -> float:
        symbols = set(previous_signals) | set(current_signals)
        return sum(abs(current_signals.get(s, 0.0) - previous_signals.get(s, 0.0)) for s in symbols)

    def build_snapshot(
        self,
        *,
        run_id: str,
        signal_values: list[float],
        forward_returns: list[float],
        ic_history: list[float],
        previous_signals: dict[str, float],
        current_signals: dict[str, float],
        candidate_count: int,
    ) -> AlphaMetricsSnapshot:
        ic = self.calculate_ic(signal_values, forward_returns)
        return AlphaMetricsSnapshot(
            run_id=run_id,
            created_at=datetime.now(UTC).isoformat(),
            information_coefficient=ic,
            ic_decay_1=self.calculate_ic_decay([*ic_history, ic]),
            signal_turnover=self.calculate_signal_turnover(previous_signals, current_signals),
            candidate_count=candidate_count,
        )
