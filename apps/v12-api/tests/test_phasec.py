from datetime import datetime, timezone

from fastapi.testclient import TestClient

from ai_hedge_bot.api.app import app
from ai_hedge_bot.core.settings import SETTINGS
from ai_hedge_bot.core.types import Signal
from ai_hedge_bot.portfolio.expected_return_model import ExpectedReturnModel
from ai_hedge_bot.portfolio.optimizer import PortfolioOptimizer

client = TestClient(app)


def _signal(sig_id: str, score: float, confidence: float = 1.0):
    return Signal(sig_id, 'BTCUSDT', datetime.now(timezone.utc), 'long', 100.0, 98.0, 104.0, score, confidence, 'x', 'momentum', 'short', 'flow', f'{sig_id}|sig')


def test_expected_return_model_monotonicity():
    model = ExpectedReturnModel()
    low = model.estimate(_signal('low', 0.2))
    high = model.estimate(_signal('high', 0.6))
    assert high.expected_return_gross > low.expected_return_gross
    assert high.expected_return_net <= high.expected_return_gross


def test_expected_return_model_caps_large_scores():
    model = ExpectedReturnModel()
    huge = model.estimate(_signal('huge', 10_000.0))
    assert huge.expected_return_gross <= SETTINGS.expected_return_cap + 1e-9
    assert huge.expected_return_net <= SETTINGS.expected_return_cap + 1e-9
    assert huge.expected_sharpe <= SETTINGS.expected_sharpe_cap + 1e-9


def test_optimizer_respects_gross_cap():
    model = ExpectedReturnModel()
    estimates = [model.estimate(_signal('a', 0.6)), model.estimate(_signal('b', 0.8))]
    weights = PortfolioOptimizer().optimize(estimates, max_gross=0.5, max_symbol_weight=0.35)
    assert sum(weights.values()) <= 0.500001
    assert max(weights.values()) <= 0.350001


def test_phasec_endpoints_after_run_once():
    rr = client.post('/run-once')
    assert rr.status_code == 200
    data = rr.json()
    assert 'phase_c' in data
    assert data['phase_c']['portfolio_risk_snapshot']['gross_exposure'] >= 0
    assert data['phase_c']['portfolio_risk_snapshot']['portfolio_expected_sharpe'] <= SETTINGS.portfolio_sharpe_cap + 1e-9

    assert client.get('/portfolio/expected-returns').status_code == 200
    assert len(client.get('/portfolio/expected-returns').json()) >= 1
    weights = client.get('/portfolio/weights')
    assert weights.status_code == 200
    assert client.get('/portfolio/allocations').status_code == 200
    risk = client.get('/portfolio/risk')
    assert risk.status_code == 200
    risk_rows = risk.json()
    assert len(risk_rows) >= 1
    latest_portfolio_id = risk_rows[0]['portfolio_id']
    current_weight_sum = sum(row['target_weight'] for row in weights.json() if row['portfolio_id'] == latest_portfolio_id)
    assert abs(current_weight_sum - risk_rows[0]['gross_exposure']) < 1e-6
    assert 'concentration_top_weight' in risk_rows[0]
    summary = client.get('/portfolio/summary')
    assert summary.status_code == 200
    assert 'portfolio_id' in summary.json()
    pnl = client.get('/portfolio/paper-pnl')
    assert pnl.status_code == 200
    assert 'fill_count' in pnl.json()


def test_runner_state_recovery_and_cycle():
    before = client.get('/runner/status')
    assert before.status_code == 200
    cycle = client.post('/runner/run-cycle')
    assert cycle.status_code == 200
    after = client.get('/runner/status').json()
    assert after['status'] == 'ok'
    assert after['cycle_count'] >= 1
