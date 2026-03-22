from fastapi.testclient import TestClient

from ai_hedge_bot.app.main import app
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.execution.planner.execution_planner import ExecutionPlanner

client = TestClient(app)


def _reset_runtime_state() -> None:
    for table in ['runtime_control_state','execution_plans','execution_fills','execution_quality_snapshots','orchestrator_runs','orchestrator_cycles','signals','signal_evaluations','portfolio_signal_decisions','portfolio_diagnostics','portfolio_positions','portfolio_snapshots','rebalance_plans','market_prices_latest','market_prices_history','position_snapshots_latest','position_snapshots_history','equity_snapshots','cash_ledger']:
        try:
            CONTAINER.runtime_store.execute(f'DELETE FROM {table}')
        except Exception:
            pass


def test_sprint6h5_orchestrator_blocked_when_halted() -> None:
    _reset_runtime_state()
    client.post('/runtime/kill-switch')
    result = client.post('/runtime/run-once?mode=paper').json()
    assert result['status'] == 'blocked'
    plans = client.get('/execution/planner/latest').json()
    assert plans['trading_state'] == 'halted'
    assert plans['plan_count'] == 0


def test_sprint6h5_planner_supports_pov_fallback_and_price_expiry() -> None:
    planner = ExecutionPlanner()
    plan = planner.build_plan(symbol='BTCUSDT', side='buy', qty=10.0, arrival_mid=100.0, bid=99.9, ask=100.1, quote_age_sec=1.0, mode='paper', participation_rate=0.2, observed_volume=5.0)
    assert plan['pov_fallback'] is True
    assert plan['algo'] == 'twap'
    assert plan['price_drift_bps'] > 0
    assert plan['routing_candidates']
