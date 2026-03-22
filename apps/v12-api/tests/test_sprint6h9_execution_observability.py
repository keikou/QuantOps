from datetime import datetime, timedelta, timezone

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


def test_sprint6h9_planner_latest_uses_execution_linked_active_definition() -> None:
    _reset_runtime_state()
    now = datetime.now(timezone.utc)
    plan_id = 'plan-observe-1'
    CONTAINER.runtime_store.append('execution_plans', {
        'plan_id': plan_id,
        'created_at': now.isoformat(),
        'run_id': 'run-observe-1',
        'mode': 'paper',
        'symbol': 'BTCUSDT',
        'side': 'buy',
        'target_weight': 0.1,
        'order_qty': 1.25,
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
    assert planner['status'] == 'ok'
    assert planner['visible_plan_count'] >= 1
    assert planner['plan_count'] == 0
    item = planner['items'][0]
    assert item['active'] is False
    assert item['activity_state'] == 'planned_only'
    assert item['plan_age_sec'] is not None

    CONTAINER.runtime_store.append('execution_orders', {
        'order_id': 'order-observe-1',
        'plan_id': plan_id,
        'parent_order_id': None,
        'client_order_id': 'client-observe-1',
        'strategy_id': 's1',
        'alpha_family': 'trend',
        'symbol': 'BTCUSDT',
        'side': 'buy',
        'order_type': 'limit',
        'qty': 1.25,
        'limit_price': 100.0,
        'venue': 'paper',
        'route': 'primary',
        'algo': 'twap',
        'submit_time': (now + timedelta(seconds=1)).isoformat(),
        'status': 'submitted',
        'source': 'planner',
        'metadata_json': '{}',
        'created_at': (now + timedelta(seconds=1)).isoformat(),
        'updated_at': (now + timedelta(seconds=1)).isoformat(),
    })
    planner2 = client.get('/execution/planner/latest').json()
    assert planner2['plan_count'] >= 1
    item2 = planner2['items'][0]
    assert item2['active'] is True
    assert item2['activity_state'] == 'executing'
    assert item2['order_count'] >= 1


def test_sprint6h9_execution_state_exposes_visible_and_submitted_counts() -> None:
    _reset_runtime_state()
    client.post('/runtime/resume')
    out = client.post('/runtime/run-once?mode=paper').json()
    assert out['status'] == 'ok'

    state = client.get('/execution/state/latest').json()
    assert state['status'] == 'ok'
    assert 'visible_plan_count' in state
    assert 'submitted_order_count' in state
    assert state['visible_plan_count'] >= state['active_plan_count']
