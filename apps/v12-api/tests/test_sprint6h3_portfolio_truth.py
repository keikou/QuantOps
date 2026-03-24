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


def test_same_symbol_multiple_strategies_remain_distinct_positions() -> None:
    _reset_runtime_state()
    truth = TruthEngine()
    truth.ensure_schema()
    truth.ensure_initial_capital()
    as_of = '2026-03-25T00:00:00'
    CONTAINER.runtime_store.append('execution_fills', [
        {
            'fill_id': 'f-strat-1',
            'run_id': 'run-a',
            'plan_id': 'plan-a',
            'strategy_id': 'trend_core',
            'alpha_family': 'trend',
            'symbol': 'BTCUSDT',
            'side': 'buy',
            'fill_qty': 0.1,
            'fill_price': 70000.0,
            'fee_bps': 0.0,
            'created_at': as_of,
        },
        {
            'fill_id': 'f-strat-2',
            'run_id': 'run-b',
            'plan_id': 'plan-b',
            'strategy_id': 'mean_reversion_core',
            'alpha_family': 'mean_reversion',
            'symbol': 'BTCUSDT',
            'side': 'sell',
            'fill_qty': 0.05,
            'fill_price': 71000.0,
            'fee_bps': 0.0,
            'created_at': '2026-03-25T00:00:01',
        },
    ])
    CONTAINER.runtime_store.append('market_prices_latest', {
        'symbol': 'BTCUSDT',
        'bid': 70490.0,
        'ask': 70510.0,
        'mid': 70500.0,
        'last': 70500.0,
        'mark_price': 70500.0,
        'source': 'test',
        'price_time': as_of,
        'quote_age_sec': 0.0,
        'stale': False,
        'fallback_reason': None,
        'updated_at': as_of,
    })
    positions = truth.rebuild_positions(as_of)
    truth.compute_equity_snapshot(positions, as_of)

    overview = client.get('/portfolio/overview').json()
    positions = overview['positions']
    btc_positions = [p for p in positions if p['symbol'] == 'BTCUSDT']

    assert len(btc_positions) == 2
    strategy_ids = {p['strategy_id'] for p in btc_positions}
    assert strategy_ids == {'trend_core', 'mean_reversion_core'}
