from datetime import datetime, timedelta, timezone
import json

from fastapi.testclient import TestClient

from ai_hedge_bot.app.main import app
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.services.truth_engine import TruthEngine

client = TestClient(app)


def _reset_runtime_state() -> None:
    for table in [
        'runtime_control_state','execution_plans','execution_fills','execution_orders','execution_quality_snapshots',
        'execution_state_snapshots','execution_block_reasons','orchestrator_runs','orchestrator_cycles','signals',
        'signal_evaluations','portfolio_signal_decisions','portfolio_diagnostics','portfolio_positions','portfolio_snapshots',
        'rebalance_plans','market_prices_latest','market_prices_history','position_snapshots_latest','position_snapshots_history',
        'position_snapshot_versions','truth_engine_state',
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


def test_sprint6h9_position_snapshots_use_active_version() -> None:
    _reset_runtime_state()
    truth = TruthEngine()
    first_as_of = datetime.now(timezone.utc).isoformat()
    CONTAINER.runtime_store.append('execution_fills', {
        'fill_id': 'fill-v1',
        'run_id': 'run-v1',
        'plan_id': 'plan-v1',
        'strategy_id': 'strategy-v1',
        'symbol': 'BTCUSDT',
        'side': 'buy',
        'fill_qty': 1.0,
        'fill_price': 100.0,
        'fee_bps': 0.0,
        'created_at': first_as_of,
    })
    CONTAINER.runtime_store.append('market_prices_latest', {
        'symbol': 'BTCUSDT',
        'mark_price': 101.0,
        'source': 'test',
        'price_time': first_as_of,
        'quote_age_sec': 0.0,
        'stale': False,
        'fallback_reason': None,
        'updated_at': first_as_of,
    })
    positions_v1 = truth.rebuild_positions(first_as_of)
    metrics_v1 = dict(truth.last_rebuild_positions_metrics)
    assert len(positions_v1) == 1
    assert metrics_v1['snapshot_version']

    second_as_of = (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat()
    CONTAINER.runtime_store.append('execution_fills', {
        'fill_id': 'fill-v2',
        'run_id': 'run-v2',
        'plan_id': 'plan-v2',
        'strategy_id': 'strategy-v1',
        'symbol': 'BTCUSDT',
        'side': 'sell',
        'fill_qty': 1.0,
        'fill_price': 102.0,
        'fee_bps': 0.0,
        'created_at': second_as_of,
    })
    positions_v2 = truth.rebuild_positions(second_as_of)
    metrics_v2 = dict(truth.last_rebuild_positions_metrics)
    assert positions_v2 == []
    assert metrics_v1['snapshot_version'] != metrics_v2['snapshot_version']
    assert metrics_v2['rebuild_mode'] == 'incremental'
    assert metrics_v2['new_fills_applied'] == 1

    active = CONTAINER.runtime_store.fetchone_dict(
        "SELECT version_id FROM position_snapshot_versions WHERE build_status = 'active' ORDER BY activated_at DESC LIMIT 1"
    )
    assert active is not None
    assert active['version_id'] == metrics_v2['snapshot_version']

    overview = client.get('/portfolio/overview').json()
    assert overview['status'] == 'ok'
    assert overview['positions'] == []


def test_sprint6h9_runtime_run_once_emits_writer_metrics() -> None:
    _reset_runtime_state()
    writer_log = CONTAINER.runtime_dir / 'logs' / 'writer_cycles.jsonl'
    if writer_log.exists():
        writer_log.unlink()

    out = client.post('/runtime/run-once?mode=paper').json()
    assert out['status'] == 'ok'
    result = out['result']
    metrics = result['details'].get('writer_metrics')
    assert metrics is not None
    assert metrics['position_snapshot_version']
    assert metrics['cycle_duration_ms'] >= 0.0

    assert writer_log.exists()
    entries = [json.loads(line) for line in writer_log.read_text(encoding='utf-8').splitlines() if line.strip()]
    assert entries
    assert any(entry['cycle_id'] == result['cycle_id'] for entry in entries)


def test_sprint6h9_equity_snapshot_reuses_watermark_when_only_prices_change() -> None:
    _reset_runtime_state()
    truth = TruthEngine()
    as_of = datetime.now(timezone.utc).isoformat()
    CONTAINER.runtime_store.append('execution_fills', {
        'fill_id': 'fill-eq-1',
        'run_id': 'run-eq-1',
        'plan_id': 'plan-eq-1',
        'strategy_id': 'strategy-eq-1',
        'alpha_family': 'trend',
        'symbol': 'BTCUSDT',
        'side': 'buy',
        'fill_qty': 1.0,
        'fill_price': 100.0,
        'fee_bps': 0.0,
        'created_at': as_of,
    })
    CONTAINER.runtime_store.append('market_prices_latest', {
        'symbol': 'BTCUSDT',
        'mark_price': 101.0,
        'source': 'test',
        'price_time': as_of,
        'quote_age_sec': 0.0,
        'stale': False,
        'fallback_reason': None,
        'updated_at': as_of,
    })

    positions_v1 = truth.rebuild_positions(as_of)
    equity_v1 = truth.compute_equity_snapshot(positions_v1, as_of)
    assert truth.last_compute_equity_snapshot_metrics['rebuild_mode'] == 'full'

    as_of_2 = (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat()
    CONTAINER.runtime_store.execute("DELETE FROM market_prices_latest WHERE symbol = 'BTCUSDT'")
    CONTAINER.runtime_store.append('market_prices_latest', {
        'symbol': 'BTCUSDT',
        'mark_price': 103.0,
        'source': 'test',
        'price_time': as_of_2,
        'quote_age_sec': 0.0,
        'stale': False,
        'fallback_reason': None,
        'updated_at': as_of_2,
    })

    positions_v2 = truth.rebuild_positions(as_of_2)
    equity_v2 = truth.compute_equity_snapshot(positions_v2, as_of_2)

    assert truth.last_rebuild_positions_metrics['rebuild_mode'] == 'incremental'
    assert truth.last_rebuild_positions_metrics['fills_scanned'] == 0
    assert truth.last_compute_equity_snapshot_metrics['rebuild_mode'] == 'incremental'
    assert truth.last_compute_equity_snapshot_metrics['fills_scanned'] == 0
    assert round(equity_v2['market_value'], 2) == 103.00
    assert round(equity_v2['total_equity'] - equity_v1['total_equity'], 2) == 2.00
