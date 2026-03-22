from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app
from ai_hedge_bot.services.truth_engine import TruthEngine

client = TestClient(app)


def _reset_runtime_state() -> None:
    for table in ['execution_fills','market_prices_latest','market_prices_history','position_snapshots_latest','position_snapshots_history','equity_snapshots','cash_ledger']:
        CONTAINER.runtime_store.execute(f'DELETE FROM {table}')


def test_margin_fields_present_and_consistent() -> None:
    _reset_runtime_state()
    truth = TruthEngine()
    truth.ensure_schema()
    truth.ensure_initial_capital()
    as_of = '2026-03-18T16:00:00'
    CONTAINER.runtime_store.append('execution_fills', [{
        'fill_id': 'f1', 'symbol': 'BTCUSDT', 'side': 'buy', 'fill_qty': 0.1, 'fill_price': 70000.0, 'fee_bps': 0.0, 'run_id': 'r1', 'strategy_id': 'r1', 'alpha_family': 'runtime', 'created_at': as_of
    }])
    truth.upsert_market_prices([{
        'symbol': 'BTCUSDT', 'bid': 70990.0, 'ask': 71010.0, 'mid': 71000.0, 'last': 71000.0, 'mark_price': 71000.0, 'source': 'test', 'quote_time': as_of, 'stale': False
    }], as_of)
    positions = truth.rebuild_positions(as_of)
    truth.compute_equity_snapshot(positions, as_of)
    overview = client.get('/portfolio/overview').json()
    assert 'collateral_equity' in overview
    assert 'available_margin' in overview
    assert 'margin_utilization' in overview
    assert round(float(overview['collateral_equity']), 2) == 100000.0
    assert round(float(overview['margin_utilization']), 4) == 0.07
