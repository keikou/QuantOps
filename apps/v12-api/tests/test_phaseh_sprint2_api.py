from fastapi.testclient import TestClient

from ai_hedge_bot.app.main import app


client = TestClient(app)


def test_health_and_overview() -> None:
    health = client.get('/system/health')
    assert health.status_code == 200
    body = health.json()
    assert body['status'] == 'ok'
    assert body['phase'] == 'H'
    assert body['sprint'] >= 2

    overview = client.get('/research-factory/overview')
    assert overview.status_code == 200
    o = overview.json()
    assert o['status'] == 'ok'
    assert o['counts']['experiments'] >= 1
    assert o['counts']['datasets'] >= 1
    assert o['counts']['features'] >= 1
    assert o['counts']['models'] >= 1


def test_research_factory_register_flow() -> None:
    dataset = client.post('/research-factory/datasets/register', json={
        'dataset_version': 'dataset.test.v2',
        'source': 'pytest',
        'symbol_scope': ['BTCUSDT', 'ETHUSDT'],
        'timeframe': '5m',
        'missing_rate': 0.02,
    })
    assert dataset.status_code == 200
    dataset_body = dataset.json()
    assert dataset_body['status'] == 'ok'
    assert dataset_body['dataset']['dataset_version'] == 'dataset.test.v2'

    feature = client.post('/research-factory/features/register', json={
        'feature_version': 'features.test.v2',
        'feature_list': ['momentum_8', 'oi_delta'],
    })
    assert feature.status_code == 200
    feature_body = feature.json()
    assert feature_body['feature']['feature_version'] == 'features.test.v2'

    experiment = client.post('/research-factory/experiments/register', json={
        'dataset_version': 'dataset.test.v2',
        'feature_version': 'features.test.v2',
        'model_version': 'xgb.test.v2',
        'strategy_id': 'trend_core',
    })
    assert experiment.status_code == 200
    exp_body = experiment.json()
    exp_id = exp_body['experiment']['experiment_id']
    assert exp_body['experiment']['immutable_record'] is True

    validation = client.post('/research-factory/validations/register', json={
        'experiment_id': exp_id,
        'summary_score': 0.81,
        'passed': True,
    })
    assert validation.status_code == 200
    val_body = validation.json()
    assert val_body['validation']['experiment_id'] == exp_id
    assert val_body['validation']['passed'] is True

    model = client.post('/research-factory/models/register', json={
        'experiment_id': exp_id,
        'dataset_version': 'dataset.test.v2',
        'feature_version': 'features.test.v2',
        'model_version': 'xgb.test.v2',
        'state': 'candidate',
    })
    assert model.status_code == 200
    model_body = model.json()
    assert model_body['model']['experiment_id'] == exp_id
    assert model_body['model']['state'] == 'candidate'
    assert len(model_body['transitions']) >= 1


def test_research_dashboard_and_openapi() -> None:
    dashboard = client.get('/dashboard/research')
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body['status'] == 'ok'
    assert body['dashboard'] == 'research'
    assert body['cards']['experiment_count'] >= 1
    assert body['cards']['model_count'] >= 1

    paths = client.get('/openapi.json').json()['paths']
    assert '/research-factory/overview' in paths
    assert '/research-factory/experiments/register' in paths
    assert '/research-factory/datasets/register' in paths
    assert '/research-factory/features/register' in paths
    assert '/research-factory/validations/register' in paths
    assert '/research-factory/models/register' in paths
