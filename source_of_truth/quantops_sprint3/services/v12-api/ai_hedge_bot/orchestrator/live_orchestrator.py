from __future__ import annotations

from ai_hedge_bot.orchestrator.base import BaseOrchestrator


class LiveOrchestrator(BaseOrchestrator):
    mode = 'live'

    def build_details(self) -> dict:
        details = super().build_details()
        details.update({
            'source': 'live_feed',
            'fills_mode': 'broker_live',
            'result_table': 'live_orders',
        })
        return details
