from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.services.truth_engine import TruthEngine


def _reset_runtime_state() -> None:
    tables = [
        'execution_fills', 'execution_orders', 'market_prices_latest', 'market_prices_history',
        'position_snapshots_latest', 'position_snapshots_history', 'equity_snapshots', 'cash_ledger',
    ]
    for table in tables:
        CONTAINER.runtime_store.execute(f'DELETE FROM {table}')


def test_cash_delta_uses_signed_qty_truth_for_sell_fill() -> None:
    _reset_runtime_state()
    truth = TruthEngine()
    truth.ensure_schema()
    truth.ensure_initial_capital()
    as_of = '2026-03-21T01:00:00'
    fills = [{
        'fill_id': 'f1', 'symbol': 'ETHUSDT', 'side': 'sell', 'fill_qty': 5.0, 'fill_price': 2000.0,
        'fee_bps': 10.0, 'run_id': 'r1', 'strategy_id': 'r1', 'alpha_family': 'runtime', 'created_at': as_of,
    }]
    truth.record_orders_and_fills(fills, as_of)
    row = CONTAINER.runtime_store.fetchone_dict('SELECT delta_cash, balance_after FROM cash_ledger ORDER BY event_time DESC LIMIT 1')
    assert round(float(row['delta_cash']), 2) == 9990.00
    assert round(float(row['balance_after']), 2) == 109990.00


def test_negative_qty_without_side_still_prices_as_short() -> None:
    _reset_runtime_state()
    truth = TruthEngine()
    truth.ensure_schema()
    truth.ensure_initial_capital()
    as_of = '2026-03-21T01:05:00'
    CONTAINER.runtime_store.append('execution_fills', [{
        'fill_id': 'f1', 'symbol': 'ETHUSDT', 'fill_qty': -5.0, 'fill_price': 2000.0,
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
    assert round(equity['total_equity'], 2) == 100500.00
