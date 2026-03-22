from fastapi.testclient import TestClient

from ai_hedge_bot.app.main import app


client = TestClient(app)


def _register_candidate() -> str:
    experiment = client.post('/research-factory/experiments/register', json={
        'dataset_version': 'dataset.s3.v1',
        'feature_version': 'features.s3.v1',
        'model_version': 'xgb.s3.v1',
        'alpha_id': 'alpha.momentum.s3',
        'strategy_id': 'trend_core',
    }).json()
    exp_id = experiment['experiment']['experiment_id']
    client.post('/research-factory/validations/register', json={
        'experiment_id': exp_id,
        'summary_score': 0.84,
        'passed': True,
    })
    model = client.post('/research-factory/models/register', json={
        'experiment_id': exp_id,
        'dataset_version': 'dataset.s3.v1',
        'feature_version': 'features.s3.v1',
        'model_version': 'xgb.s3.v1',
        'validation_metrics': {'summary_score': 0.84, 'max_drawdown': 0.08},
        'state': 'candidate',
    }).json()
    return model['model']['model_id']


def test_governance_endpoints_and_overview() -> None:
    health = client.get('/system/health')
    assert health.status_code == 200
    assert health.json()['sprint'] >= 3

    model_id = _register_candidate()

    promotion = client.post('/research-factory/promotion/evaluate', json={
        'model_id': model_id,
        'sample_size': 180,
        'regime_coverage': 0.86,
        'promotion_score_min': 0.75,
    })
    assert promotion.status_code == 200
    p_body = promotion.json()
    assert p_body['status'] == 'ok'
    assert p_body['promotion']['decision'] in {'approve', 'needs_review', 'reject'}

    live_review = client.get('/research-factory/live-review')
    assert live_review.status_code == 200
    lr_body = live_review.json()
    assert lr_body['review']['decision'] in {'keep', 'reduce_capital', 'shadow', 'rollback'}

    decay = client.get('/research-factory/alpha-decay')
    assert decay.status_code == 200
    d_body = decay.json()
    assert d_body['decay']['severity'] in {'stable', 'medium', 'high'}

    rollback = client.post('/research-factory/rollback/evaluate', json={'model_id': model_id})
    assert rollback.status_code == 200
    rb_body = rollback.json()
    assert rb_body['rollback']['action'] in {'hold', 'rollback'}

    cc = client.post('/research-factory/champion-challenger/run', json={})
    assert cc.status_code == 200
    cc_body = cc.json()
    assert cc_body['run']['winner'] in {'champion', 'challenger'}

    overview = client.get('/research-factory/governance-overview')
    assert overview.status_code == 200
    o_body = overview.json()
    assert o_body['status'] == 'ok'
    assert len(o_body['promotions']) >= 1
    assert len(o_body['live_reviews']) >= 1
    assert len(o_body['decay_events']) >= 1
    assert len(o_body['rollback_events']) >= 1
    assert len(o_body['champion_challenger_runs']) >= 1


def test_research_dashboard_and_openapi_include_sprint3() -> None:
    dashboard = client.get('/dashboard/research')
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body['status'] == 'ok'
    assert body['cards']['latest_promotion_decision'] is not None
    assert body['cards']['latest_live_review_decision'] is not None
    assert body['cards']['latest_decay_severity'] is not None

    paths = client.get('/openapi.json').json()['paths']
    assert '/research-factory/governance-overview' in paths
    assert '/research-factory/promotion/evaluate' in paths
    assert '/research-factory/live-review' in paths
    assert '/research-factory/alpha-decay' in paths
    assert '/research-factory/rollback/evaluate' in paths
    assert '/research-factory/champion-challenger/run' in paths
