from fastapi.testclient import TestClient

from ai_hedge_bot.app.main import app


client = TestClient(app)


def test_system_and_sprint1_routes_still_work() -> None:
    assert client.get('/system/health').status_code == 200
    assert client.post('/signals/generate').status_code == 200
    assert client.post('/portfolio/prepare').status_code == 200


def test_orchestrator_modes_and_latest_run() -> None:
    for path, mode in (
        ('/orchestrator/backtest/run', 'backtest'),
        ('/orchestrator/paper/run-cycle', 'paper'),
        ('/orchestrator/shadow/run-cycle', 'shadow'),
    ):
        res = client.post(path)
        assert res.status_code == 200
        body = res.json()
        assert body['status'] == 'ok'
        assert body['mode'] == mode
        assert body['run_id']
        assert body['cycle_id']
        assert 'details' in body

    latest = client.get('/orchestrator/runs/latest')
    assert latest.status_code == 200
    latest_body = latest.json()
    assert latest_body['status'] == 'ok'
    assert latest_body['run']['mode'] == 'shadow'


def test_snapshot_save_restore_and_execution_quality() -> None:
    client.post('/portfolio/prepare')
    client.post('/orchestrator/shadow/run-cycle')

    save = client.post('/orchestrator/state/snapshot/save')
    assert save.status_code == 200
    assert save.json()['status'] == 'ok'

    latest = client.get('/orchestrator/state/snapshot/latest')
    assert latest.status_code == 200
    latest_body = latest.json()
    assert latest_body['status'] == 'ok'
    assert 'snapshot' in latest_body
    assert latest_body['snapshot']['latest_orchestrator_run']['mode'] == 'shadow'

    restore = client.post('/orchestrator/state/snapshot/restore')
    assert restore.status_code == 200
    restore_body = restore.json()
    assert restore_body['status'] == 'ok'
    assert restore_body['snapshot']['latest_portfolio_diagnostics']['kept_signals'] >= 1

    quality = client.get('/execution/quality/latest')
    assert quality.status_code == 200
    quality_body = quality.json()
    assert quality_body['status'] == 'ok'
    assert quality_body['mode'] == 'shadow'
    assert quality_body['fill_rate'] is not None

    quality_summary = client.get('/execution/quality/latest_summary')
    assert quality_summary.status_code == 200
    quality_summary_body = quality_summary.json()
    assert quality_summary_body['status'] == 'ok'
    assert quality_summary_body['mode'] == 'shadow'
    assert quality_summary_body['fill_rate'] is not None
    assert 'latest_fills' not in quality_summary_body
    assert 'latest_plans' not in quality_summary_body
