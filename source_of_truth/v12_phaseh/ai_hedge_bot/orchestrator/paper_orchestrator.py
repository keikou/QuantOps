from __future__ import annotations

from ai_hedge_bot.orchestrator.base import BaseOrchestrator


class PaperOrchestrator(BaseOrchestrator):
    mode = 'paper'

    def build_details(self) -> dict:
        details = super().build_details()
        details.update({
            'source': 'live_feed_or_synthetic',
            'fills_mode': 'paper',
            'result_table': 'paper_pnl_snapshots',
        })
        return details
