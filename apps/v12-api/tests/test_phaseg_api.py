from fastapi.testclient import TestClient
from ai_hedge_bot.api.app import app

client = TestClient(app)


def test_system_health():
    res = client.get('/system/health')
    assert res.status_code == 200
    body = res.json()
    assert body['status'] == 'ok'
    assert body['phase'] == 'G'


def test_market_routes():
    assert client.get('/market/data-quality').status_code == 200
    assert client.get('/market/feed-liveness').status_code == 200


def test_signal_and_portfolio_routes():
    sig = client.post('/signals/generate')
    assert sig.status_code == 200
    assert 'signals' in sig.json()
    port = client.post('/portfolio/prepare')
    assert port.status_code == 200
    assert 'decisions' in port.json()


def test_orchestrator_routes():
    assert client.post('/orchestrator/backtest/run').status_code == 200
    assert client.post('/orchestrator/paper/run-cycle').status_code == 200
    assert client.post('/orchestrator/shadow/run-cycle').status_code == 200


def test_analytics_and_dashboard_routes():
    assert client.get('/analytics/signal-summary').status_code == 200
    assert client.get('/analytics/portfolio-summary').status_code == 200
    assert client.get('/analytics/shadow-summary').status_code == 200
    assert client.get('/analytics/execution-quality').status_code == 200
    assert client.get('/dashboard/research').status_code == 200
    assert client.get('/dashboard/portfolio').status_code == 200
    assert client.get('/dashboard/execution').status_code == 200
    assert client.get('/dashboard/global').status_code == 200
