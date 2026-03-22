from __future__ import annotations

from typing import Any


class StrategyBudgetAllocator:
    def rank_strategies(self, strategy_stats: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(
            strategy_stats,
            key=lambda x: (float(x.get('sharpe', 0.0)), -float(x.get('drawdown', 0.0))),
            reverse=True,
        )

    def allocate_strategy_risk_budget(self, strategy_stats: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ranked = self.rank_strategies(strategy_stats)
        if not ranked:
            return []
        scores: list[float] = []
        for row in ranked:
            sharpe = max(0.0, float(row.get('sharpe', 0.0)))
            dd = max(0.0, float(row.get('drawdown', 0.0)))
            scores.append(max(0.0, sharpe * (1.0 - dd)))
        total = sum(scores)
        if total <= 0:
            equal_budget = 1.0 / len(ranked)
            return [{**row, 'risk_budget': equal_budget} for row in ranked]
        return [{**row, 'risk_budget': score / total} for row, score in zip(ranked, scores)]
