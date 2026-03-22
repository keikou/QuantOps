from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app

client = TestClient(app)


def _reset_runtime_tables() -> None:
    tables = [
        'runtime_control_state', 'execution_state_snapshots', 'execution_block_reasons',
        'runtime_runs', 'runtime_run_steps', 'scheduler_runs', 'runtime_checkpoints', 'audit_logs',
        'signals', 'signal_evaluations', 'alpha_signal_snapshots', 'alpha_candidates',
        'portfolio_signal_decisions', 'portfolio_diagnostics', 'portfolio_snapshots', 'portfolio_positions', 'rebalance_plans',
        'execution_plans', 'execution_fills', 'execution_quality_snapshots', 'shadow_orders', 'shadow_fills', 'shadow_pnl_snapshots',
        'orchestrator_runs', 'orchestrator_cycles', 'market_prices_latest', 'market_prices_history',
        'position_snapshots_latest', 'position_snapshots_history', 'equity_snapshots', 'cash_ledger', 'execution_orders',
    ]
    for table in tables:
        CONTAINER.runtime_store.execute(f'DELETE FROM {table}')


def test_runtime_execution_and_portfolio_expose_quote_truth_metadata() -> None:
    _reset_runtime_tables()
    response = client.post('/runtime/run-once')
    assert response.status_code == 200

    fills = client.get('/execution/fills').json()
    assert fills['items']
    first_fill = fills['items'][0]
    assert 'price_source' in first_fill
    assert 'arrival_mid_price' in first_fill
    assert 'quote_time' in first_fill

    portfolio = client.get('/portfolio/overview').json()
    assert 'quotes_as_of' in portfolio
    assert 'stale_positions' in portfolio
    assert portfolio['positions']
    first_position = portfolio['positions'][0]
    assert 'price_source' in first_position
    assert 'quote_time' in first_position
    assert 'quote_age_sec' in first_position
    assert 'stale' in first_position
