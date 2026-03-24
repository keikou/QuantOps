from datetime import datetime, timezone

from fastapi.testclient import TestClient

from ai_hedge_bot.app.main import app
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.api.routes import execution as execution_routes


client = TestClient(app)


def _reset_runtime_state() -> None:
    execution_routes._execution_view_cache['expires_at'] = None
    execution_routes._execution_view_cache['key'] = None
    execution_routes._execution_view_cache['payload'] = None
    for table in [
        'runtime_control_state', 'execution_plans', 'execution_fills', 'execution_orders',
        'execution_quality_snapshots', 'execution_state_snapshots', 'execution_block_reasons',
    ]:
        try:
            CONTAINER.runtime_store.execute(f'DELETE FROM {table}')
        except Exception:
            pass


def test_execution_planner_and_state_expose_freshness_metadata() -> None:
    _reset_runtime_state()
    now = datetime.now(timezone.utc).isoformat()
    CONTAINER.runtime_store.append('execution_plans', {
        'plan_id': 'plan-meta-1',
        'created_at': now,
        'run_id': 'run-meta-1',
        'mode': 'paper',
        'symbol': 'BTCUSDT',
        'side': 'buy',
        'target_weight': 0.1,
        'order_qty': 1.0,
        'limit_price': 100.0,
        'participation_rate': 0.1,
        'status': 'planned',
        'algo': 'twap',
        'route': 'primary',
        'expire_seconds': 120,
        'slice_count': 1,
        'metadata_json': '{}',
    })

    planner = client.get('/execution/planner/latest').json()
    state = client.get('/execution/state/latest').json()

    assert planner['status'] == 'ok'
    assert planner['build_status'] in {'live', 'fresh_cache'}
    assert planner['source_snapshot_time'] == planner['as_of']
    assert 'data_freshness_sec' in planner

    assert state['status'] == 'ok'
    assert state['build_status'] in {'live', 'fresh_cache'}
    assert state['source_snapshot_time'] == state['as_of']
    assert 'data_freshness_sec' in state
