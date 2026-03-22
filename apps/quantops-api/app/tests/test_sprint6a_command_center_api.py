from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_command_center_overview_route() -> None:
    res = client.get('/api/v1/command-center/overview')
    assert res.status_code == 200
    body = res.json()
    assert body['status'] == 'ok'
    assert 'portfolio_value' in body
    assert 'fill_rate' in body
    assert 'system_status' in body


def test_command_center_read_only_routes() -> None:
    assert client.get('/api/v1/command-center/strategies').status_code == 200
    assert client.get('/api/v1/command-center/execution/latest').status_code == 200
    assert client.get('/api/v1/command-center/portfolio/summary').status_code == 200
    assert client.get('/api/v1/command-center/risk/summary').status_code == 200
    assert client.get('/api/v1/command-center/system/summary').status_code == 200
    assert client.get('/api/v1/command-center/system/jobs').status_code == 200
    assert client.get('/api/v1/command-center/system/alerts').status_code == 200
