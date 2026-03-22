from __future__ import annotations

from ai_hedge_bot.orchestrator.base import BaseOrchestrator


class BacktestOrchestrator(BaseOrchestrator):
    mode = 'backtest'

    def build_details(self) -> dict:
        details = super().build_details()
        details.update({
            'source': 'replay',
            'fills_mode': 'simulated_historical',
            'result_table': 'backtest_results',
        })
        return details
