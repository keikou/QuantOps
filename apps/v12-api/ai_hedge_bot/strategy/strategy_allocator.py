from __future__ import annotations

from typing import Any

from ai_hedge_bot.risk.global_risk_engine import GlobalRiskEngine
from ai_hedge_bot.strategy.capital_allocator import CapitalAllocator
from ai_hedge_bot.strategy.cross_strategy_netting import CrossStrategyNetting
from ai_hedge_bot.strategy.risk_budget_engine import RiskBudgetEngine


class StrategyAllocator:
    def __init__(self) -> None:
        self.capital_allocator = CapitalAllocator()
        self.netting = CrossStrategyNetting()
        self.risk_budget = RiskBudgetEngine()
        self.global_risk = GlobalRiskEngine()

    def run(self) -> dict[str, Any]:
        allocation_bundle = self.capital_allocator.allocate()
        netting_bundle = self.netting.evaluate(allocation_bundle['allocations'], allocation_bundle['targets_by_strategy'])
        risk_bundle = self.risk_budget.build(allocation_bundle['allocations'], netting_bundle)
        global_alerts = self.global_risk.assess(risk_bundle)
        return {
            'status': 'ok',
            'generated_at': allocation_bundle['generated_at'],
            'allocations': allocation_bundle['allocations'],
            'allocation_totals': allocation_bundle['totals'],
            'targets_by_strategy': allocation_bundle['targets_by_strategy'],
            'netting': netting_bundle,
            'risk': risk_bundle,
            'global_risk': global_alerts,
        }
