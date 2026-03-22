from fastapi.testclient import TestClient

from ai_hedge_bot.app.main import app


client = TestClient(app)


def test_sprint3_analytics_routes() -> None:
    client.post('/signals/generate')
    client.post('/portfolio/prepare')
    client.post('/orchestrator/shadow/run-cycle')

    for path in (
        '/analytics/signal-summary',
        '/analytics/portfolio-summary',
        '/analytics/shadow-summary',
        '/analytics/execution-quality',
        '/analytics/mode-comparison',
    ):
        res = client.get(path)
        assert res.status_code == 200
        body = res.json()
        assert body['status'] == 'ok'


def test_sprint3_dashboard_routes() -> None:
    for path, expected in (
        ('/dashboard/research', 'research'),
        ('/dashboard/portfolio', 'portfolio'),
        ('/dashboard/execution', 'execution'),
        ('/dashboard/global', 'global'),
    ):
        res = client.get(path)
        assert res.status_code == 200
        body = res.json()
        assert body['status'] == 'ok'
        assert body['dashboard'] == expected
        assert 'cards' in body


def test_openapi_includes_phaseg_surface() -> None:
    res = client.get('/openapi.json')
    assert res.status_code == 200
    paths = res.json()['paths']
    assert '/analytics/signal-summary' in paths
    assert '/dashboard/global' in paths


def test_sprint3_data_linkage_moves_counts() -> None:
    client.post('/signals/generate')
    client.post('/portfolio/prepare')
    client.post('/orchestrator/shadow/run-cycle')

    signal = client.get('/analytics/signal-summary').json()
    execution = client.get('/analytics/execution-quality').json()
    dashboard = client.get('/dashboard/global').json()

    assert signal['signals_evaluated'] >= 1
    assert signal['signal_count'] >= 1
    assert execution['fill_rate'] is not None
    assert execution['avg_slippage_bps'] is not None
    assert dashboard['cards']['signal_count'] >= 1
    assert dashboard['cards']['fill_rate'] is not None
