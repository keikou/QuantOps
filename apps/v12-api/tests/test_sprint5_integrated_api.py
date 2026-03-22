from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app

client = TestClient(app)


def _clean_runtime_tables() -> None:
    tables = [
        'runtime_runs', 'runtime_run_steps', 'scheduler_runs', 'runtime_checkpoints', 'audit_logs',
        'risk_snapshots', 'analytics_performance', 'analytics_alpha_metrics', 'strategy_risk_budgets', 'regime_states',
        'runtime_mode_runs', 'validation_results', 'incidents', 'shadow_pnl_snapshots',
    ]
    for table in tables:
        try:
            CONTAINER.runtime_store.execute(f'DELETE FROM {table}')
        except Exception:
            pass


def test_sprint5_integrated_runtime_and_mode_endpoints() -> None:
    _clean_runtime_tables()
    r = client.post('/runtime/run-once')
    assert r.status_code == 200
    run_id = r.json()['run_id']

    detail = client.get(f'/runtime/runs/{run_id}')
    assert detail.status_code == 200
    payload = detail.json()['item']
    assert payload['status'] == 'success'
    assert 'audit_logs' in payload

    risk = client.get('/risk/latest')
    assert risk.status_code == 200

    perf = client.get('/analytics/performance')
    assert perf.status_code == 200

    regime = client.get('/governance/regime')
    assert regime.status_code == 200

    modes = client.get('/runtime/modes')
    assert modes.status_code == 200
    current = client.get('/runtime/modes/current')
    assert current.status_code == 200


def test_sprint5d_run_with_mode_and_acceptance() -> None:
    _clean_runtime_tables()
    blocked = client.post('/runtime/run-with-mode', json={'mode': 'live_ready'})
    assert blocked.status_code == 200
    body = blocked.json()
    assert body['runtime_mode'] == 'live_ready'
    assert body['status'] in {'blocked', 'ok'}

    acceptance = client.get('/acceptance/status')
    assert acceptance.status_code == 200

    incidents = client.get('/incidents/latest')
    assert incidents.status_code == 200

    shadow = client.post('/runtime/run-with-mode', json={'mode': 'shadow'})
    assert shadow.status_code == 200
    shadow_summary = client.get('/analytics/shadow-summary')
    assert shadow_summary.status_code == 200
