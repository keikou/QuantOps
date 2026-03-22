from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_sprint5c_quantops_routes():
    assert client.get('/api/v1/risk/latest').status_code == 200
    assert client.get('/api/v1/risk/history').status_code == 200
    assert client.get('/api/v1/analytics/performance').status_code == 200
    assert client.get('/api/v1/analytics/alpha').status_code == 200
    assert client.get('/api/v1/governance/budgets').status_code == 200
    assert client.get('/api/v1/governance/regime').status_code == 200
    assert client.get('/api/v1/scheduler/jobs').status_code == 200
    assert client.get('/api/v1/scheduler/runs').status_code == 200
