from __future__ import annotations

from typing import Any

from ai_hedge_bot.analytics.strategy_analytics import StrategyAnalytics
from ai_hedge_bot.strategy.strategy_allocator import StrategyAllocator
from ai_hedge_bot.strategy.strategy_registry import StrategyRegistry


class StrategyService:
    def __init__(self) -> None:
        self.registry = StrategyRegistry()
        self.allocator = StrategyAllocator()
        self.analytics = StrategyAnalytics()

    def registry_view(self) -> dict[str, Any]:
        strategies = self.registry.list()
        return {
            'status': 'ok',
            'strategy_count': len(strategies),
            'enabled_count': sum(1 for row in strategies if row.get('enabled')),
            'strategies': strategies,
        }

    def allocate_capital(self) -> dict[str, Any]:
        result = self.allocator.run()
        self.analytics.record_from_allocation(result)
        result['strategy_summary'] = self.analytics.summary()
        return result

    def latest_risk_budget(self) -> dict[str, Any]:
        summary = self.analytics.summary()
        if summary.get('latest_risk_snapshot'):
            return {'status': 'ok', 'risk': summary['latest_risk_snapshot'], 'global': summary.get('latest_global_risk', {})}
        result = self.allocate_capital()
        return {'status': 'ok', 'risk': result['risk'], 'global': result['global_risk']}
