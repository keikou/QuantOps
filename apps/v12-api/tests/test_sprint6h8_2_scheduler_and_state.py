from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app

client = TestClient(app)


def _reset_tables() -> None:
    tables = [
        'runtime_control_state', 'execution_orders', 'execution_fills', 'execution_plans',
        'execution_state_snapshots', 'execution_block_reasons', 'scheduler_jobs'
    ]
    for table in tables:
        try:
            CONTAINER.runtime_store.execute(f'DELETE FROM {table}')
        except Exception:
            pass


def test_execution_state_forces_halted_zero_open_counts() -> None:
    _reset_tables()
    CONTAINER.runtime_store.append('execution_plans', {
        'plan_id': 'p1', 'created_at': '2026-03-19T00:00:00Z', 'run_id': 'r1', 'mode': 'paper',
        'symbol': 'BTCUSDT', 'side': 'buy', 'target_weight': 0.1, 'order_qty': 1.0, 'limit_price': 100000.0,
        'participation_rate': 0.1, 'status': 'planned', 'algo': 'twap', 'route': 'maker_bias', 'expire_seconds': 60, 'slice_count': 2, 'metadata_json': '{}'
    })
    CONTAINER.runtime_store.append('execution_orders', {
        'order_id': 'o1', 'plan_id': 'p1', 'parent_order_id': 'p1', 'client_order_id': 'o1', 'strategy_id': 'r1', 'alpha_family': 'runtime',
        'symbol': 'BTCUSDT', 'side': 'buy', 'order_type': 'paper_twap', 'qty': 1.0, 'limit_price': 100000.0, 'venue': 'paper_simulator',
        'route': 'maker_bias', 'algo': 'twap', 'submit_time': '2026-03-19T00:00:00Z', 'status': 'submitted', 'source': 'test', 'metadata_json': '{}',
        'created_at': '2026-03-19T00:00:00Z', 'updated_at': '2026-03-19T00:00:00Z'
    })
    client.post('/runtime/kill-switch')
    resp = client.get('/execution/state/latest')
    body = resp.json()
    assert body['trading_state'] == 'halted'
    assert body['execution_state'] in {'halted', 'blocked'}
    assert body['open_order_count'] == 0
    assert body['submitted_order_count'] == 0
    assert body['active_plan_count'] == 0
