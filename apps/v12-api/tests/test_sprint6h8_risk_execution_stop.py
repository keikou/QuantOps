from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app


client = TestClient(app)


def _reset_runtime_tables() -> None:
    tables = [
        'runtime_control_state', 'execution_orders', 'execution_fills', 'execution_plans',
        'execution_quality_snapshots', 'execution_state_snapshots', 'execution_block_reasons',
        'runtime_runs', 'runtime_run_steps', 'scheduler_runs', 'runtime_checkpoints', 'audit_logs',
        'signals', 'signal_evaluations', 'alpha_signal_snapshots', 'alpha_candidates',
        'portfolio_signal_decisions', 'portfolio_diagnostics', 'portfolio_snapshots', 'portfolio_positions', 'rebalance_plans',
        'shadow_orders', 'shadow_fills', 'shadow_pnl_snapshots', 'orchestrator_runs', 'orchestrator_cycles',
    ]
    for table in tables:
        try:
            CONTAINER.runtime_store.execute(f'DELETE FROM {table}')
        except Exception:
            pass


def test_kill_switch_cancels_open_orders_and_blocks_new_execution() -> None:
    _reset_runtime_tables()

    CONTAINER.runtime_store.append('execution_orders', {
        'order_id': 'o1',
        'plan_id': 'p1',
        'parent_order_id': 'p1',
        'client_order_id': 'o1',
        'strategy_id': 'test',
        'alpha_family': 'runtime',
        'symbol': 'BTCUSDT',
        'side': 'buy',
        'order_type': 'limit',
        'qty': 1.0,
        'limit_price': 100000.0,
        'venue': 'paper_simulator',
        'route': 'maker_bias',
        'algo': 'twap',
        'submit_time': '2026-03-19T00:00:00Z',
        'status': 'submitted',
        'source': 'test',
        'metadata_json': '{}',
        'created_at': '2026-03-19T00:00:00Z',
        'updated_at': '2026-03-19T00:00:00Z',
    })

    kill = client.post('/runtime/kill-switch')
    assert kill.status_code == 200
    kill_body = kill.json()
    assert kill_body['status'] == 'ok'
    assert kill_body['trading_state'] == 'halted'
    assert kill_body['cancelled_open_orders'] == 1

    order = CONTAINER.runtime_store.fetchone_dict("SELECT status FROM execution_orders WHERE order_id = 'o1'")
    assert order is not None
    assert order['status'] == 'cancelled'

    run = client.post('/runtime/run-once?mode=paper')
    assert run.status_code == 200
    run_body = run.json()
    assert run_body['status'] == 'blocked'
    assert run_body['trading_state'] == 'halted'

    state = client.get('/execution/state/latest')
    assert state.status_code == 200
    state_body = state.json()
    assert str(state_body['trading_state']).lower() == 'halted'
    assert str(state_body['execution_state']).lower() in {'halted', 'blocked'}

    reason = client.get('/execution/block-reasons/latest')
    assert reason.status_code == 200
    items = reason.json()['items']
    assert items
    assert items[0]['code'] == 'risk_halted'
