from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app

client = TestClient(app)


def _reset_runtime_state() -> None:
    tables = [
        'runtime_runs', 'runtime_run_steps', 'scheduler_runs', 'runtime_checkpoints', 'audit_logs',
        'signals', 'signal_evaluations', 'alpha_signal_snapshots', 'alpha_candidates',
        'portfolio_signal_decisions', 'portfolio_diagnostics', 'portfolio_snapshots', 'portfolio_positions', 'rebalance_plans',
        'execution_plans', 'execution_fills', 'execution_quality_snapshots', 'shadow_orders', 'shadow_fills', 'shadow_pnl_snapshots',
        'orchestrator_runs', 'orchestrator_cycles', 'market_prices_latest', 'market_prices_history', 'execution_orders',
        'position_snapshots_latest', 'position_snapshots_history', 'equity_snapshots', 'cash_ledger',
    ]
    for table in tables:
        CONTAINER.runtime_store.execute(f'DELETE FROM {table}')


def test_two_runtime_cycles_rebalance_instead_of_stacking() -> None:
    _reset_runtime_state()
    first = client.post('/runtime/run-once')
    assert first.status_code == 200
    second = client.post('/runtime/run-once')
    assert second.status_code == 200

    positions_payload = client.get('/portfolio/positions/latest')
    assert positions_payload.status_code == 200
    positions = positions_payload.json()['items']
    assert positions
    gross_weight = sum(abs(float(item['weight'])) for item in positions)
    assert gross_weight < 1.5

    overview = client.get('/portfolio/overview').json()
    assert float(overview['gross_exposure']) < 1.5
    assert float(overview['total_equity']) > 0.0
