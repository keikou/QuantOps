from fastapi.testclient import TestClient

from ai_hedge_bot.app.main import app


client = TestClient(app)


def test_alpha_factory_generate_test_evaluate_flow() -> None:
    health = client.get('/system/health')
    assert health.status_code == 200
    assert health.json()['sprint'] == 4

    generated = client.post('/alpha/generate', json={
        'alpha_family': 'derivatives',
        'factor_type': 'carry',
        'feature_dependencies': ['funding_rate', 'oi_delta'],
        'turnover_profile': 'medium',
    })
    assert generated.status_code == 200
    g_body = generated.json()
    alpha_id = g_body['alpha']['alpha_id']
    assert g_body['alpha']['state'] == 'generated'

    tested = client.post('/alpha/test', json={'alpha_id': alpha_id, 'signal_strength': 0.82})
    assert tested.status_code == 200
    t_body = tested.json()
    assert t_body['result']['alpha_id'] == alpha_id
    assert t_body['result']['decision'] in {'pass', 'shadow', 'research'}

    ranked = client.post('/alpha/evaluate', json={'alpha_id': alpha_id})
    assert ranked.status_code == 200
    r_body = ranked.json()
    assert r_body['ranking']['alpha_id'] == alpha_id
    assert r_body['ranking']['recommended_action'] in {'promote', 'shadow', 'research'}


def test_alpha_library_dashboard_and_openapi() -> None:
    overview = client.get('/alpha/overview')
    assert overview.status_code == 200
    o_body = overview.json()
    assert o_body['status'] == 'ok'
    assert o_body['counts']['registry'] >= 1

    registry = client.get('/alpha/registry')
    assert registry.status_code == 200
    assert len(registry.json()['registry']) >= 1

    ranking = client.get('/alpha/ranking')
    assert ranking.status_code == 200
    assert len(ranking.json()['ranking']) >= 1

    library = client.get('/alpha/library')
    assert library.status_code == 200
    assert len(library.json()['library']) >= 1

    dashboard = client.get('/dashboard/alpha-factory')
    assert dashboard.status_code == 200
    d_body = dashboard.json()
    assert d_body['status'] == 'ok'
    assert d_body['cards']['registry_count'] >= 1
    assert d_body['cards']['top_alpha_id'] is not None

    global_dash = client.get('/dashboard/global')
    assert global_dash.status_code == 200
    assert global_dash.json()['cards']['alpha_registry_count'] >= 1

    paths = client.get('/openapi.json').json()['paths']
    assert '/alpha/overview' in paths
    assert '/alpha/generate' in paths
    assert '/alpha/test' in paths
    assert '/alpha/evaluate' in paths
    assert '/alpha/ranking' in paths
    assert '/alpha/library' in paths
    assert '/dashboard/alpha-factory' in paths
