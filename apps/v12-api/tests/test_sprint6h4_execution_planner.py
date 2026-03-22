from fastapi.testclient import TestClient

from ai_hedge_bot.app.main import app
from ai_hedge_bot.app.container import CONTAINER

client = TestClient(app)


def _reset_runtime_state() -> None:
    for table in ['runtime_control_state','execution_plans','execution_fills','execution_quality_snapshots','orchestrator_runs','orchestrator_cycles','signals','signal_evaluations','portfolio_signal_decisions','portfolio_diagnostics','portfolio_positions','portfolio_snapshots','rebalance_plans','market_prices_latest','market_prices_history','position_snapshots_latest','position_snapshots_history','equity_snapshots','cash_ledger']:
        try:
            CONTAINER.runtime_store.execute(f'DELETE FROM {table}')
        except Exception:
            pass


def test_sprint6h4_runtime_kill_switch_blocks_run_once() -> None:
    _reset_runtime_state()
    blocked = client.post('/runtime/kill-switch').json()
    assert blocked['trading_state'] == 'halted'
    result = client.post('/runtime/run-once?mode=paper').json()
    assert result['status'] == 'blocked'
    assert result['blocked'] is True


def test_sprint6h4_execution_planner_persists_algo_route_expiry() -> None:
    _reset_runtime_state()
    client.post('/runtime/resume')
    result = client.post('/runtime/run-once?mode=paper').json()
    assert result['status'] == 'ok'
    plans = client.get('/execution/plans').json()
    assert plans['items']
    first = plans['items'][0]
    assert first['algo'] in {'twap', 'pov', 'aggressive_limit'}
    assert first['route'] in {'primary', 'split_book', 'maker_bias'}
    assert int(first['expire_seconds']) > 0
    assert int(first['slice_count']) >= 1
