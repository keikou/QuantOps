from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app

client = TestClient(app)


def _reset_runtime_tables() -> None:
    tables = [
        'runtime_control_state', 'execution_state_snapshots', 'execution_block_reasons',
        'runtime_runs', 'runtime_run_steps', 'scheduler_runs', 'runtime_checkpoints', 'audit_logs',
        'signals', 'signal_evaluations', 'alpha_signal_snapshots', 'alpha_candidates',
        'portfolio_signal_decisions', 'portfolio_diagnostics', 'portfolio_snapshots', 'portfolio_positions', 'rebalance_plans',
        'execution_plans', 'execution_fills', 'execution_quality_snapshots', 'shadow_orders', 'shadow_fills', 'shadow_pnl_snapshots',
        'orchestrator_runs', 'orchestrator_cycles',
    ]
    for table in tables:
        CONTAINER.runtime_store.execute(f'DELETE FROM {table}')


def test_runtime_run_once_persists_full_pipeline() -> None:
    _reset_runtime_tables()
    response = client.post('/runtime/run-once')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    run_id = payload['run_id']

    detail = client.get(f'/runtime/runs/{run_id}')
    assert detail.status_code == 200
    item = detail.json()['item']
    assert item['status'] == 'success'
    assert len(item['steps']) == 1
    assert len(item['checkpoints']) == 1
    assert len(item['audit_logs']) >= 3

    signal_snapshot = client.get('/strategy/signals/latest').json()
    assert signal_snapshot['snapshot']['run_id'] == run_id
    assert signal_snapshot['snapshot']['signal_count'] > 0
    assert len(signal_snapshot['items']) == signal_snapshot['snapshot']['signal_count']

    portfolio = client.get('/portfolio/overview').json()
    assert portfolio['snapshot']['run_id'] == run_id
    assert portfolio['snapshot']['target_count'] == len(portfolio['positions'])
    assert portfolio['snapshot']['gross_exposure'] > 0

    execution = client.get('/execution/quality/latest').json()
    assert execution['run_id'] == run_id
    assert execution['order_count'] == execution['fill_count']
    assert len(execution['latest_fills']) == execution['fill_count']


def test_scheduler_routes_show_seeded_jobs_and_runs() -> None:
    _reset_runtime_tables()
    client.post('/runtime/run-once')
    jobs = client.get('/scheduler/jobs')
    assert jobs.status_code == 200
    assert len(jobs.json()['items']) >= 2

    runs = client.get('/scheduler/runs')
    assert runs.status_code == 200
    assert len(runs.json()['items']) >= 1
