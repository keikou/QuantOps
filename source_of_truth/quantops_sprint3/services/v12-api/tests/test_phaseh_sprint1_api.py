from fastapi.testclient import TestClient

from ai_hedge_bot.app.main import app


client = TestClient(app)


def test_health_and_registry() -> None:
    res = client.get('/system/health')
    assert res.status_code == 200
    body = res.json()
    assert body['status'] == 'ok'
    assert body['phase'] == 'H'
    assert body['sprint'] >= 1

    registry = client.get('/strategy/registry')
    assert registry.status_code == 200
    reg_body = registry.json()
    assert reg_body['status'] == 'ok'
    assert reg_body['strategy_count'] >= 3
    assert reg_body['enabled_count'] >= 2


def test_strategy_allocation_and_risk_budget() -> None:
    client.post('/signals/generate')
    allocation = client.post('/strategy/allocate-capital')
    assert allocation.status_code == 200
    body = allocation.json()
    assert body['status'] == 'ok'
    assert len(body['allocations']) >= 3
    assert body['allocation_totals']['capital_allocated'] > 0
    assert body['netting']['gross_before'] >= body['netting']['gross_after']
    assert body['risk']['gross_exposure'] >= 0

    risk = client.get('/strategy/risk-budget')
    assert risk.status_code == 200
    risk_body = risk.json()
    assert risk_body['status'] == 'ok'
    assert 'per_strategy' in risk_body['risk']
    assert len(risk_body['risk']['per_strategy']) >= 3


def test_strategy_analytics_and_dashboard() -> None:
    client.post('/signals/generate')
    client.post('/strategy/allocate-capital')

    analytics = client.get('/analytics/strategy-summary')
    assert analytics.status_code == 200
    body = analytics.json()
    assert body['status'] == 'ok'
    assert body['aggregate']['strategy_count'] >= 3
    assert len(body['strategies']) >= 3

    dashboard = client.get('/dashboard/global')
    assert dashboard.status_code == 200
    dash = dashboard.json()
    assert dash['status'] == 'ok'
    assert dash['dashboard'] == 'global'
    assert dash['cards']['strategy_count'] >= 3
    assert 'strategy' in dash


def test_openapi_contains_phaseh_routes() -> None:
    paths = client.get('/openapi.json').json()['paths']
    assert '/strategy/registry' in paths
    assert '/strategy/allocate-capital' in paths
    assert '/strategy/risk-budget' in paths
    assert '/analytics/strategy-summary' in paths
