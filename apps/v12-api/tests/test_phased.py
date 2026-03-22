from fastapi.testclient import TestClient

from ai_hedge_bot.api.app import app

client = TestClient(app)


def test_health_reports_phase_d():
    res = client.get('/health')
    assert res.status_code == 200
    assert res.json()['phase'] == 'D'


def test_phase_d_endpoints_after_run_once():
    rr = client.post('/run-once')
    assert rr.status_code == 200
    data = rr.json()
    assert 'phase_d' in data
    assert data['phase_d']['shadow_order_count'] >= 1
    assert client.get('/analytics/shadow-summary').status_code == 200
    assert client.get('/analytics/execution-quality').status_code == 200
    assert client.get('/analytics/slippage-report').status_code == 200
    lifecycle = client.get('/analytics/order-lifecycle')
    assert lifecycle.status_code == 200
    assert len(lifecycle.json()) >= 2
    orders = client.get('/execution/shadow-orders')
    assert orders.status_code == 200
    assert len(orders.json()) >= 1
    fills = client.get('/execution/shadow-fills')
    assert fills.status_code == 200
    assert len(fills.json()) >= 1
    latency = client.get('/execution/latency')
    assert latency.status_code == 200
    assert len(latency.json()) >= 1
