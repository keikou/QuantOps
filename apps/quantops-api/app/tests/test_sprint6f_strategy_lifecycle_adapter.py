from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_sprint6f_start_stop_are_adapter_backed() -> None:
    start = client.post('/api/v1/command-center/strategies/start', json={'strategy_id': 's1'})
    assert start.status_code == 200
    payload = start.json()
    assert payload['ok'] is True
    assert payload['details']['ok'] is True
    assert payload['details']['runtime_state']['remote_status'] in {'ok', 'accepted', 'submitted', 'queued'}

    stop = client.post('/api/v1/command-center/strategies/stop', json={'strategy_id': 's1'})
    assert stop.status_code == 200
    payload = stop.json()
    assert payload['ok'] is True
    assert payload['details']['ok'] is True
    assert payload['details']['runtime_state']['remote_status'] in {'ok', 'accepted', 'submitted', 'queued'}

    strategies = client.get('/api/v1/command-center/strategies')
    assert strategies.status_code == 200
    s1 = next(item for item in strategies.json()['items'] if item['strategy_id'] == 's1')
    assert s1['remote_status'] in {'ok', 'accepted', 'submitted', 'queued'}
