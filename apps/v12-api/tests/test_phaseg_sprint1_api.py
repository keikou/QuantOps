from fastapi.testclient import TestClient

from ai_hedge_bot.app.main import app


client = TestClient(app)


def test_system_health() -> None:
    res = client.get('/system/health')
    assert res.status_code == 200
    body = res.json()
    assert body['status'] == 'ok'
    assert body['phase'] == 'G'


def test_market_collect_and_normalize() -> None:
    collect = client.post('/market/collect/run')
    assert collect.status_code == 200
    collect_body = collect.json()
    assert collect_body['status'] == 'ok'
    assert collect_body['batch_size'] >= 1

    normalize = client.post('/market/normalize/run')
    assert normalize.status_code == 200
    norm_body = normalize.json()
    assert norm_body['status'] == 'ok'
    assert norm_body['batch_size'] == collect_body['batch_size']
    assert all('timestamp' in item for item in norm_body['items'])


def test_signal_generation() -> None:
    res = client.post('/signals/generate')
    assert res.status_code == 200
    body = res.json()
    assert body['status'] == 'ok'
    assert body['count'] >= 1
    first = body['signals'][0]
    assert first['dominant_alpha'] == 'phaseg_meta_alpha'
    assert first['alpha_family'] == 'cross_sectional'


def test_portfolio_prepare_and_diagnostics() -> None:
    prepared = client.post('/portfolio/prepare')
    assert prepared.status_code == 200
    body = prepared.json()
    assert body['status'] == 'ok'
    assert body['diagnostics']['kept_signals'] >= 1
    assert len(body['decisions']) == body['diagnostics']['kept_signals']

    diag = client.get('/portfolio/diagnostics/latest')
    assert diag.status_code == 200
    diag_body = diag.json()
    assert diag_body['status'] == 'ok'
    assert diag_body['diagnostics']['kept_signals'] == body['diagnostics']['kept_signals']
