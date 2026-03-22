from __future__ import annotations

from ai_hedge_bot.core.ids import new_cycle_id, new_run_id
from ai_hedge_bot.core.clock import utc_now_iso


class BaseOrchestrator:
    mode = 'unknown'

    def build_details(self) -> dict:
        return {
            'data_ready': True,
            'signals_ready': True,
            'portfolio_ready': True,
            'execution_interface': 'simulated',
        }

    def run_cycle(self) -> dict:
        run_id = new_run_id()
        cycle_id = new_cycle_id()
        return {
            'status': 'ok',
            'mode': self.mode,
            'run_id': run_id,
            'cycle_id': cycle_id,
            'timestamp': utc_now_iso(),
            'details': self.build_details(),
        }
