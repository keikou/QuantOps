from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.services.truth_engine import TruthEngine


def _reset_runtime_state() -> None:
    tables = [
        'execution_fills', 'execution_orders', 'market_prices_latest', 'market_prices_history',
        'position_snapshots_latest', 'position_snapshots_history', 'position_snapshot_versions',
        'equity_snapshots', 'cash_ledger', 'truth_engine_state',
    ]
    for table in tables:
        try:
            CONTAINER.runtime_store.execute(f'DELETE FROM {table}')
        except Exception:
            pass


def test_signed_qty_short_keeps_equity_near_initial_plus_pnl() -> None:
    _reset_runtime_state()
    truth = TruthEngine()
    truth.ensure_schema()
    truth.ensure_initial_capital()
    as_of = '2026-03-21T00:00:00'
    CONTAINER.runtime_store.append('execution_fills', [{
        'fill_id': 'f1', 'symbol': 'ETHUSDT', 'side': 'sell', 'fill_qty': 5.0, 'fill_price': 2000.0,
        'fee_bps': 0.0, 'run_id': 'r1', 'strategy_id': 'r1', 'alpha_family': 'runtime', 'created_at': as_of,
    }])
    truth.upsert_market_prices([{
        'symbol': 'ETHUSDT', 'bid': 1899.0, 'ask': 1901.0, 'mid': 1900.0, 'last': 1900.0,
        'mark_price': 1900.0, 'source': 'test', 'quote_time': as_of, 'stale': False,
    }], as_of)
    positions = truth.rebuild_positions(as_of)
    equity = truth.compute_equity_snapshot(positions, as_of)

    assert round(equity['cash_balance'], 2) == 110000.00
    assert round(equity['market_value'], 2) == -9500.00
    assert round(equity['unrealized_pnl'], 2) == 500.00
    assert round(equity['total_equity'], 2) == 100500.00
    assert round(equity['available_margin'], 2) == 90500.00


def test_signed_qty_mixed_long_short_uses_cash_plus_market_value() -> None:
    _reset_runtime_state()
    truth = TruthEngine()
    truth.ensure_schema()
    truth.ensure_initial_capital()
    as_of = '2026-03-21T00:05:00'
    fills = [
        {
            'fill_id': 'f1', 'symbol': 'BTCUSDT', 'side': 'buy', 'fill_qty': 0.1, 'fill_price': 70000.0,
            'fee_bps': 0.0, 'run_id': 'r1', 'strategy_id': 'r1', 'alpha_family': 'runtime', 'created_at': as_of,
        },
        {
            'fill_id': 'f2', 'symbol': 'ETHUSDT', 'side': 'sell', 'fill_qty': 5.0, 'fill_price': 2000.0,
            'fee_bps': 0.0, 'run_id': 'r1', 'strategy_id': 'r1', 'alpha_family': 'runtime', 'created_at': as_of,
        },
    ]
    CONTAINER.runtime_store.append('execution_fills', fills)
    truth.upsert_market_prices([
        {
            'symbol': 'BTCUSDT', 'bid': 70990.0, 'ask': 71010.0, 'mid': 71000.0, 'last': 71000.0,
            'mark_price': 71000.0, 'source': 'test', 'quote_time': as_of, 'stale': False,
        },
        {
            'symbol': 'ETHUSDT', 'bid': 1899.0, 'ask': 1901.0, 'mid': 1900.0, 'last': 1900.0,
            'mark_price': 1900.0, 'source': 'test', 'quote_time': as_of, 'stale': False,
        },
    ], as_of)
    positions = truth.rebuild_positions(as_of)
    equity = truth.compute_equity_snapshot(positions, as_of)

    assert round(equity['cash_balance'], 2) == 103000.00
    assert round(equity['market_value'], 2) == -2400.00
    assert round(equity['unrealized_pnl'], 2) == 600.00
    assert round(equity['total_equity'], 2) == 100600.00
    assert round(equity['used_margin'], 2) == 17000.00
    assert round(equity['available_margin'], 2) == 83600.00
