from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app
from ai_hedge_bot.api.routes import portfolio as portfolio_routes
from ai_hedge_bot.api.routes import runtime as runtime_routes

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

    summary = client.get('/execution/quality/latest_summary').json()
    assert summary['run_id'] == run_id
    assert summary['order_count'] == execution['order_count']
    assert summary['fill_count'] == execution['fill_count']
    assert 'latest_fills' not in summary
    assert 'latest_plans' not in summary


def test_scheduler_routes_show_seeded_jobs_and_runs() -> None:
    _reset_runtime_tables()
    client.post('/runtime/run-once')
    jobs = client.get('/scheduler/jobs')
    assert jobs.status_code == 200
    assert len(jobs.json()['items']) >= 2

    runs = client.get('/scheduler/runs')
    assert runs.status_code == 200
    assert len(runs.json()['items']) >= 1


def test_runtime_runs_route_reuses_short_ttl_cache(monkeypatch) -> None:
    runtime_routes._runtime_runs_cache.clear()
    call_count = {'count': 0}

    def fake_list_runs(*, limit: int = 20) -> list[dict]:
        call_count['count'] += 1
        return [{'run_id': f'run-{call_count["count"]}', 'created_at': '2026-03-23T00:00:00Z'}]

    monkeypatch.setattr(runtime_routes._service, 'list_runs', fake_list_runs)

    first = client.get('/runtime/runs?limit=5')
    second = client.get('/runtime/runs?limit=5')
    third = client.get('/runtime/runs?limit=10')

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 200
    assert first.json()['items'] == second.json()['items']
    assert first.json()['items'] != third.json()['items']
    assert call_count['count'] == 2


def test_portfolio_equity_history_reuses_short_ttl_cache_by_limit(monkeypatch) -> None:
    portfolio_routes._equity_history_cache.clear()
    call_count = {'count': 0}

    def fake_fetchall_dict(query: str, params=None):
        call_count['count'] += 1
        limit = int((params or [0])[0] or 0)
        return [
            {
                'snapshot_time': f'2026-03-24T00:00:{limit:02d}+00:00',
                'total_equity': float(limit),
                'pnl': float(limit) / 10.0,
                'drawdown': 0.0,
            }
        ]

    monkeypatch.setattr(CONTAINER.runtime_store, 'fetchall_dict', fake_fetchall_dict)

    first = client.get('/portfolio/equity-history?limit=20')
    second = client.get('/portfolio/equity-history?limit=20')
    third = client.get('/portfolio/equity-history?limit=10')

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 200
    assert first.json() == second.json()
    assert first.json() != third.json()
    assert call_count['count'] == 2
