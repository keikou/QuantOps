from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_sprint5d_quantops_routes():
    assert client.get('/api/v1/modes/current').status_code == 200
    assert client.get('/api/v1/modes/config').status_code == 200
    assert client.get('/api/v1/acceptance/status').status_code == 200
    assert client.get('/api/v1/acceptance/checks').status_code == 200
    assert client.post('/api/v1/acceptance/run').status_code == 200
    assert client.get('/api/v1/incidents/latest').status_code == 200
    assert client.get('/api/v1/incidents/history').status_code == 200
    assert client.post('/api/v1/scheduler/run-now', params={'mode':'shadow'}).status_code == 200
