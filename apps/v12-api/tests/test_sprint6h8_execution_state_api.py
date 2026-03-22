from fastapi.testclient import TestClient

from ai_hedge_bot.app.main import app
from ai_hedge_bot.app.container import CONTAINER

client = TestClient(app)


def _reset_runtime_state() -> None:
    for table in [
        'runtime_control_state','execution_plans','execution_fills','execution_orders','execution_quality_snapshots',
        'execution_state_snapshots','execution_block_reasons','orchestrator_runs','orchestrator_cycles','signals',
        'signal_evaluations','portfolio_signal_decisions','portfolio_diagnostics','portfolio_positions','portfolio_snapshots',
        'rebalance_plans','market_prices_latest','market_prices_history','position_snapshots_latest','position_snapshots_history',
        'equity_snapshots','cash_ledger'
    ]:
        try:
            CONTAINER.runtime_store.execute(f'DELETE FROM {table}')
        except Exception:
            pass


def test_sprint6h8_orders_state_and_block_reasons_exist_after_run() -> None:
    _reset_runtime_state()
    client.post('/runtime/resume')
    out = client.post('/runtime/run-once?mode=paper').json()
    assert out['status'] == 'ok'

    orders = client.get('/execution/orders').json()
    assert orders['status'] == 'ok'
    assert len(orders['items']) >= 1
    assert orders['items'][0]['order_id']
    assert orders['items'][0]['plan_id']

    state = client.get('/execution/state/latest').json()
    assert state['status'] == 'ok'
    assert state['execution_state'] in {'planned', 'submitted', 'partially_filled', 'filled', 'degraded'}
    assert state['active_plan_count'] >= 1

    reasons = client.get('/execution/block-reasons/latest').json()
    assert reasons['status'] == 'ok'
    assert isinstance(reasons['items'], list)


def test_sprint6h8_halted_state_reports_risk_halted_reason() -> None:
    _reset_runtime_state()
    client.post('/runtime/kill-switch')
    state = client.get('/execution/state/latest').json()
    assert state['execution_state'] == 'halted'
    reasons = client.get('/execution/block-reasons/latest').json()['items']
    codes = {item['code'] for item in reasons}
    assert 'risk_halted' in codes
