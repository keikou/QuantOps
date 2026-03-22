from fastapi.testclient import TestClient

from ai_hedge_bot.api.app import app


client = TestClient(app)


def test_sprint5c_run_and_read_endpoints():
    payload = {
        'run_id': 'test_s5c_001',
        'positions': [
            {'symbol': 'BTCUSDT', 'weight': 0.10, 'side': 'long', 'sector': 'crypto', 'strategy_id': 'mom_01'},
            {'symbol': 'ETHUSDT', 'weight': -0.04, 'side': 'short', 'sector': 'crypto', 'strategy_id': 'mr_01'},
        ],
        'current_equity': 101000.0,
        'previous_equity': 100000.0,
        'previous_peak_equity': 103000.0,
        'return_history': [0.01, -0.003, 0.004],
        'equity_curve': [100000.0, 101000.0, 100700.0],
        'previous_weights': {'BTCUSDT': 0.08, 'ETHUSDT': -0.02},
        'current_weights': {'BTCUSDT': 0.10, 'ETHUSDT': -0.04},
        'signal_values': [0.8, -0.3, 0.4],
        'forward_returns': [0.02, -0.01, 0.01],
        'ic_history': [0.03, 0.02],
        'previous_signals': {'BTCUSDT': 0.5},
        'current_signals': {'BTCUSDT': 0.8, 'ETHUSDT': -0.3},
        'candidate_count': 12,
        'strategy_stats': [
            {'strategy_id': 'mom_01', 'sharpe': 1.5, 'drawdown': 0.05},
            {'strategy_id': 'mr_01', 'sharpe': 0.9, 'drawdown': 0.08},
        ],
        'avg_cross_asset_correlation': 0.45,
        'trend_score': 0.70,
    }
    run_resp = client.post('/runtime/run-sprint5c', json=payload)
    assert run_resp.status_code == 200
    assert run_resp.json()['run_id'] == 'test_s5c_001'

    assert client.get('/risk/latest').status_code == 200
    assert client.get('/risk/history').status_code == 200
    assert client.get('/analytics/performance').status_code == 200
    assert client.get('/analytics/alpha').status_code == 200
    assert client.get('/governance/budgets').status_code == 200
    assert client.get('/governance/regime').status_code == 200
