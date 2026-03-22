from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_command_center_strategy_control_routes() -> None:
    start = client.post('/api/v1/command-center/strategies/start', json={'strategy_id': 's1'})
    assert start.status_code == 200
    assert start.json()['ok'] is True

    update = client.post('/api/v1/command-center/strategies/risk', json={'strategy_id': 's1', 'risk_budget': 0.22, 'note': 'Sprint6C test'})
    assert update.status_code == 200
    assert update.json()['ok'] is True

    stop = client.post('/api/v1/command-center/strategies/stop', json={'strategy_id': 's1'})
    assert stop.status_code == 200
    assert stop.json()['ok'] is True

    strategies = client.get('/api/v1/command-center/strategies')
    assert strategies.status_code == 200
    first = next((item for item in strategies.json()['items'] if item['strategy_id'] == 's1'), None)
    assert first is not None
    assert first['status'] == 'stopped'
    assert first['risk_budget'] == 0.22


def test_command_center_global_risk_control_routes() -> None:
    pause = client.post('/api/v1/command-center/risk/pause', json={'note': 'maintenance'})
    assert pause.status_code == 200
    assert pause.json()['ok'] is True

    summary = client.get('/api/v1/command-center/risk/summary')
    assert summary.status_code == 200
    assert summary.json()['trading_state'] == 'paused'

    resume = client.post('/api/v1/command-center/risk/resume', json={'note': 'resume'})
    assert resume.status_code == 200
    assert resume.json()['ok'] is True

    summary_after = client.get('/api/v1/command-center/risk/summary')
    assert summary_after.status_code == 200
    assert summary_after.json()['trading_state'] == 'running'

    kill = client.post('/api/v1/command-center/risk/kill-switch', json={'note': 'critical breach'})
    assert kill.status_code == 200
    assert kill.json()['ok'] is True
