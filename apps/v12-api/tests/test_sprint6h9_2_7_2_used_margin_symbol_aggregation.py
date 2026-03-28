from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.services.truth_engine import TruthEngine


def _reset_runtime_state() -> None:
    for table in [
        'execution_fills', 'execution_orders', 'market_prices_latest', 'market_prices_history',
        'position_snapshots_latest', 'position_snapshots_history', 'position_snapshot_versions',
        'equity_snapshots', 'cash_ledger', 'truth_engine_state',
    ]:
        try:
            CONTAINER.runtime_store.execute(f'DELETE FROM {table}')
        except Exception:
            pass


def test_used_margin_rollup_nets_same_symbol_entry_notional() -> None:
    rollup = TruthEngine._summarize_positions_for_equity([
        {
            'symbol': 'BTCUSDT',
            'strategy_id': 's1',
            'alpha_family': 'trend',
            'signed_qty': 5.0,
            'abs_qty': 5.0,
            'side': 'long',
            'avg_entry_price': 100.0,
            'market_value': 500.0,
            'unrealized_pnl': 0.0,
            'realized_pnl': 0.0,
        },
        {
            'symbol': 'BTCUSDT',
            'strategy_id': 's2',
            'alpha_family': 'mean_reversion',
            'signed_qty': -4.0,
            'abs_qty': 4.0,
            'side': 'short',
            'avg_entry_price': 110.0,
            'market_value': -400.0,
            'unrealized_pnl': 0.0,
            'realized_pnl': 0.0,
        },
    ])

    assert round(rollup['used_margin'], 2) == 60.0
    assert round(rollup['current_long_notional'], 2) == 100.0
    assert round(rollup['current_short_notional'], 2) == 0.0
    assert round(rollup['market_value'], 2) == 100.0


def test_compute_equity_snapshot_uses_symbol_aggregated_used_margin_truth() -> None:
    _reset_runtime_state()
    truth = TruthEngine()
    truth.ensure_schema()
    truth.ensure_initial_capital()
    as_of = '2026-03-28T01:00:00'

    fills = [
        {
            'fill_id': 'f1', 'symbol': 'BTCUSDT', 'side': 'buy', 'fill_qty': 5.0, 'fill_price': 100.0,
            'fee_bps': 0.0, 'run_id': 'r1', 'strategy_id': 'strategy-long', 'alpha_family': 'trend', 'created_at': as_of,
        },
        {
            'fill_id': 'f2', 'symbol': 'BTCUSDT', 'side': 'sell', 'fill_qty': 4.0, 'fill_price': 110.0,
            'fee_bps': 0.0, 'run_id': 'r2', 'strategy_id': 'strategy-short', 'alpha_family': 'mean_reversion', 'created_at': as_of,
        },
    ]
    CONTAINER.runtime_store.append('execution_fills', fills)
    truth.upsert_market_prices([{
        'symbol': 'BTCUSDT', 'bid': 99.0, 'ask': 101.0, 'mid': 100.0, 'last': 100.0,
        'mark_price': 100.0, 'source': 'test', 'quote_time': as_of, 'stale': False,
    }], as_of)

    positions = truth.rebuild_positions(as_of)
    equity = truth.compute_equity_snapshot(positions, as_of)

    assert round(equity['cash_balance'], 2) == 99940.0
    assert round(equity['market_value'], 2) == 100.0
    assert round(equity['total_equity'], 2) == 100040.0
    assert round(equity['used_margin'], 2) == 60.0
    assert round(equity['available_margin'], 2) == 99980.0
