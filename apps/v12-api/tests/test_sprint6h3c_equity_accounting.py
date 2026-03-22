from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app
from ai_hedge_bot.services.truth_engine import TruthEngine

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


def test_equity_uses_free_cash_plus_used_margin_plus_unrealized() -> None:
    _reset_runtime_state()
    truth = TruthEngine()
    truth.ensure_schema()
    truth.ensure_initial_capital()
    as_of = "2026-03-18T16:00:00"
    fills = [
        {
            "fill_id": "f1", "symbol": "BTCUSDT", "side": "buy", "fill_qty": 0.1, "fill_price": 70000.0, "fee_bps": 0.0,
            "run_id": "r1", "strategy_id": "r1", "alpha_family": "runtime",
        },
        {
            "fill_id": "f2", "symbol": "ETHUSDT", "side": "sell", "fill_qty": 5.0, "fill_price": 2000.0, "fee_bps": 0.0,
            "run_id": "r1", "strategy_id": "r1", "alpha_family": "runtime",
        },
    ]
    CONTAINER.runtime_store.append('execution_fills', [{**fill, 'created_at': as_of} for fill in fills])
    truth.upsert_market_prices([
        {"symbol": "BTCUSDT", "bid": 7099.0*10, "ask": 7101.0*10, "mid": 71000.0, "last": 71000.0, "mark_price": 71000.0, "source": "test", "quote_time": as_of, "stale": False},
        {"symbol": "ETHUSDT", "bid": 1899.0, "ask": 1901.0, "mid": 1900.0, "last": 1900.0, "mark_price": 1900.0, "source": "test", "quote_time": as_of, "stale": False},
    ], as_of)
    positions = truth.rebuild_positions(as_of)
    equity = truth.compute_equity_snapshot(positions, as_of)
    assert round(equity['used_margin'], 2) == 17000.00
    assert round(equity['free_cash'], 2) == 83000.00
    assert round(equity['unrealized_pnl'], 2) == 600.00
    assert round(equity['total_equity'], 2) == 100600.00
    overview = client.get('/portfolio/overview').json()
    assert round(float(overview['free_cash']), 2) == 83000.00
    assert round(float(overview['used_margin']), 2) == 17000.00
    assert round(float(overview['total_equity']), 2) == 100600.00
