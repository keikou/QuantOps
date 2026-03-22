from fastapi.testclient import TestClient
from ai_hedge_bot.api.app import app

client = TestClient(app)


def test_health_endpoint():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'


def test_feature_schema_endpoint():
    r = client.get('/features/schema')
    assert r.status_code == 200
    assert r.json()['count'] == 40


def test_alpha_registry_endpoint():
    r = client.get('/alpha/registry')
    assert r.status_code == 200
    assert r.json()['count'] == 20


def test_run_once_and_analytics_endpoints():
    rr = client.post('/run-once')
    assert rr.status_code == 200
    data = rr.json()
    assert 'signals' in data
    assert 'alpha_performance' in data
    assert client.get('/analytics/alpha-performance').status_code == 200
    assert client.get('/analytics/regime-performance').status_code == 200
    pd_resp = client.get('/analytics/portfolio-diagnostics')
    assert pd_resp.status_code == 200
    assert isinstance(pd_resp.json(), list)
    assert len(pd_resp.json()) >= 1
    assert client.get('/analytics/weight-history').status_code == 200


def test_portfolio_diagnostics_normalization_hides_legacy_flattened_keys(tmp_path):
    import json

    from ai_hedge_bot.analytics.portfolio_analytics import load_portfolio_diagnostics
    from ai_hedge_bot.data.storage.duckdb_store import DuckDBStore

    log_dir = tmp_path / 'logs'
    log_dir.mkdir(parents=True)
    log_path = log_dir / 'portfolio_diagnostics.jsonl'
    log_path.write_text(
        "\n".join([
            json.dumps({
                'timestamp': '',
                'input_signal_count': 2,
                'selected_count': 1,
                'family_concentration.derivatives': 0.7,
                'selected_count_by_family.derivatives': 1,
                'feature_counts.BTCUSDT': 40,
            }),
            json.dumps({
                'timestamp': '2026-03-11T18:35:10+00:00',
                'input_signal_count': 5,
                'selected_count': 2,
                'family_concentration': {'derivatives': 0.45, 'momentum': 0.25},
                'selected_count_by_family': {'derivatives': 1, 'momentum': 1},
                'feature_counts': {'BTCUSDT': 40, 'ETHUSDT': 40},
            }),
        ]) + "\n",
        encoding='utf-8',
    )
    store = DuckDBStore(tmp_path / 'analytics.duckdb')
    store.sync_jsonl('portfolio_diagnostics', log_path)

    rows = load_portfolio_diagnostics(store)
    assert len(rows) == 1
    assert rows[0]['timestamp'] == '2026-03-11T18:35:10+00:00'
    assert rows[0]['family_concentration_by_family'] == {'derivatives': 0.45, 'momentum': 0.25}
    assert rows[0]['selected_count_by_family'] == {'derivatives': 1, 'momentum': 1}
    assert rows[0]['feature_counts'] == {'BTCUSDT': 40, 'ETHUSDT': 40}
    assert 'family_concentration.derivatives' not in rows[0]
    assert 'selected_count_by_family.derivatives' not in rows[0]
    assert 'feature_counts.BTCUSDT' not in rows[0]


def test_cleanup_script_normalizes_legacy_portfolio_rows(tmp_path):
    import json

    from tools.cleanup_portfolio_diagnostics import cleanup_file

    log_path = tmp_path / 'portfolio_diagnostics.jsonl'
    log_path.write_text(
        json.dumps({
            'timestamp': '',
            'family_concentration.derivatives': 0.6,
            'selected_count_by_family.derivatives': 2,
            'feature_counts.BTCUSDT': 40,
        }) + "\n",
        encoding='utf-8',
    )

    cleaned = cleanup_file(log_path)
    assert cleaned == 1

    row = json.loads(log_path.read_text(encoding='utf-8').strip())
    assert row['timestamp'] != ''
    assert row['family_concentration'] == {'derivatives': 0.6}
    assert row['selected_count_by_family'] == {'derivatives': 2}
    assert row['feature_counts'] == {'BTCUSDT': 40}
    assert 'family_concentration.derivatives' not in row
    assert 'selected_count_by_family.derivatives' not in row
    assert 'feature_counts.BTCUSDT' not in row


def test_portfolio_diagnostics_sorts_newest_first_when_all_rows_have_timestamps(tmp_path):
    import json

    from ai_hedge_bot.analytics.portfolio_analytics import load_portfolio_diagnostics
    from ai_hedge_bot.data.storage.duckdb_store import DuckDBStore

    log_dir = tmp_path / 'logs'
    log_dir.mkdir(parents=True)
    log_path = log_dir / 'portfolio_diagnostics.jsonl'
    log_path.write_text(
        "\n".join([
            json.dumps({'timestamp': '2026-03-11T18:29:40+00:00', 'selected_count': 1}),
            json.dumps({'timestamp': '2026-03-11T18:51:30+00:00', 'selected_count': 3}),
        ]) + "\n",
        encoding='utf-8',
    )
    store = DuckDBStore(tmp_path / 'analytics.duckdb')
    store.sync_jsonl('portfolio_diagnostics', log_path)

    rows = load_portfolio_diagnostics(store)
    assert [row['timestamp'] for row in rows] == [
        '2026-03-11T18:51:30+00:00',
        '2026-03-11T18:29:40+00:00',
    ]
