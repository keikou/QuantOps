from __future__ import annotations

import json
from pathlib import Path

from ai_hedge_bot.core.utils import utc_now
from ai_hedge_bot.services.trading_service import TradingService


class ContinuousPaperRunner:
    def __init__(self, service: TradingService, state_path: Path) -> None:
        self.service = service
        self.state_path = state_path
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def load_state(self) -> dict:
        if not self.state_path.exists():
            return {'cycle_count': 0, 'last_run_at': None, 'status': 'idle'}
        try:
            return json.loads(self.state_path.read_text(encoding='utf-8'))
        except Exception:
            return {'cycle_count': 0, 'last_run_at': None, 'status': 'corrupt_state_recovered'}

    def save_state(self, state: dict) -> None:
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')

    def run_cycle(self) -> dict:
        state = self.load_state()
        result = self.service.run_once()
        state['cycle_count'] = int(state.get('cycle_count', 0)) + 1
        state['last_run_at'] = utc_now().isoformat()
        state['status'] = 'ok'
        state['last_portfolio_id'] = result.get('phase_c', {}).get('portfolio_id')
        self.save_state(state)
        return {'runner_state': state, 'run_result': result}
