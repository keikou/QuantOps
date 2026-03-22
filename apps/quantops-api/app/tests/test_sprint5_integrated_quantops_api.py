from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_quantops_sprint5_integrated_routes() -> None:
    assert client.get('/api/v1/modes/current').status_code == 200
    assert client.get('/api/v1/modes/config').status_code == 200
    assert client.get('/api/v1/acceptance/status').status_code == 200
    assert client.get('/api/v1/incidents/latest').status_code == 200
    assert client.get('/api/v1/risk/latest').status_code == 200
    assert client.get('/api/v1/analytics/performance').status_code == 200
    assert client.get('/api/v1/governance/regime').status_code == 200
    assert client.post('/api/v1/scheduler/run-now', params={'mode': 'paper'}).status_code == 200
