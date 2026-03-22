from __future__ import annotations

from ai_hedge_bot.orchestrator.base import BaseOrchestrator


class ShadowOrchestrator(BaseOrchestrator):
    mode = 'shadow'

    def build_details(self) -> dict:
        details = super().build_details()
        details.update({
            'source': 'live_feed_or_synthetic',
            'fills_mode': 'shadow_execution',
            'result_table': 'execution_quality_snapshots',
        })
        return details
