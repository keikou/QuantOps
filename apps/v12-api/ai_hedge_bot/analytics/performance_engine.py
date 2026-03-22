from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from statistics import mean, pstdev
from typing import Any


@dataclass(slots=True)
class PerformanceSnapshot:
    run_id: str
    created_at: str
    daily_return: float
    cumulative_return: float
    volatility: float
    sharpe: float
    sortino: float
    max_drawdown: float
    turnover: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PerformanceEngine:
    def calculate_daily_return(self, previous_equity: float, current_equity: float) -> float:
        if previous_equity <= 0:
            return 0.0
        return (current_equity - previous_equity) / previous_equity

    def calculate_cum_return(self, returns: list[float]) -> float:
        value = 1.0
        for r in returns:
            value *= 1.0 + r
        return value - 1.0

    def calculate_volatility(self, returns: list[float], annualization: int = 252) -> float:
        if len(returns) <= 1:
            return 0.0
        return pstdev(returns) * sqrt(annualization)

    def calculate_sharpe(self, returns: list[float], risk_free_rate: float = 0.0) -> float:
        if len(returns) <= 1:
            return 0.0
        excess = [r - risk_free_rate / 252 for r in returns]
        vol = pstdev(excess)
        if vol == 0:
            return 0.0
        return mean(excess) / vol * sqrt(252)

    def calculate_sortino(self, returns: list[float], risk_free_rate: float = 0.0) -> float:
        if not returns:
            return 0.0
        excess = [r - risk_free_rate / 252 for r in returns]
        downside = [min(0.0, r) for r in excess]
        downside_sq = [x * x for x in downside]
        denom = (sum(downside_sq) / len(downside_sq)) ** 0.5 if downside_sq else 0.0
        if denom == 0:
            return 0.0
        return mean(excess) / denom * sqrt(252)

    def calculate_max_drawdown(self, equity_curve: list[float]) -> float:
        if not equity_curve:
            return 0.0
        peak = equity_curve[0]
        max_dd = 0.0
        for value in equity_curve:
            peak = max(peak, value)
            if peak > 0:
                max_dd = max(max_dd, (peak - value) / peak)
        return max_dd

    def calculate_turnover(self, previous_weights: dict[str, float], current_weights: dict[str, float]) -> float:
        symbols = set(previous_weights) | set(current_weights)
        return 0.5 * sum(abs(current_weights.get(s, 0.0) - previous_weights.get(s, 0.0)) for s in symbols)
