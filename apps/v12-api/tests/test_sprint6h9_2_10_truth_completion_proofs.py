from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.services.truth_engine import TruthEngine


def _reset_runtime_state() -> None:
    for table in [
        "execution_fills",
        "execution_orders",
        "market_prices_latest",
        "market_prices_history",
        "position_snapshots_latest",
        "position_snapshots_history",
        "position_snapshot_versions",
        "equity_snapshots",
        "cash_ledger",
        "truth_engine_state",
    ]:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def _seed_truth_inputs() -> None:
    fills = [
        {
            "fill_id": "f-001",
            "run_id": "run-a",
            "plan_id": "plan-a",
            "strategy_id": "trend-core",
            "alpha_family": "trend",
            "symbol": "BTCUSDT",
            "side": "buy",
            "fill_qty": 0.6,
            "fill_price": 65000.0,
            "fee_bps": 0.0,
            "created_at": "2026-03-28T10:00:00",
        },
        {
            "fill_id": "f-002",
            "run_id": "run-b",
            "plan_id": "plan-b",
            "strategy_id": "mr-core",
            "alpha_family": "mean_reversion",
            "symbol": "BTCUSDT",
            "side": "sell",
            "fill_qty": 0.2,
            "fill_price": 65200.0,
            "fee_bps": 0.0,
            "created_at": "2026-03-28T10:01:00",
        },
        {
            "fill_id": "f-003",
            "run_id": "run-a",
            "plan_id": "plan-c",
            "strategy_id": "trend-core",
            "alpha_family": "trend",
            "symbol": "ETHUSDT",
            "side": "buy",
            "fill_qty": 4.0,
            "fill_price": 2000.0,
            "fee_bps": 0.0,
            "created_at": "2026-03-28T10:02:00",
        },
        {
            "fill_id": "f-004",
            "run_id": "run-c",
            "plan_id": "plan-d",
            "strategy_id": "carry-core",
            "alpha_family": "carry",
            "symbol": "ETHUSDT",
            "side": "sell",
            "fill_qty": 1.5,
            "fill_price": 2015.0,
            "fee_bps": 0.0,
            "created_at": "2026-03-28T10:03:00",
        },
        {
            "fill_id": "f-005",
            "run_id": "run-d",
            "plan_id": "plan-e",
            "strategy_id": "trend-core",
            "alpha_family": "trend",
            "symbol": "DOGEUSDT",
            "side": "buy",
            "fill_qty": 10000.0,
            "fill_price": 0.09,
            "fee_bps": 0.0,
            "created_at": "2026-03-28T10:04:00",
        },
        {
            "fill_id": "f-006",
            "run_id": "run-e",
            "plan_id": "plan-f",
            "strategy_id": "hedge-core",
            "alpha_family": "hedge",
            "symbol": "DOGEUSDT",
            "side": "sell",
            "fill_qty": 3000.0,
            "fill_price": 0.091,
            "fee_bps": 0.0,
            "created_at": "2026-03-28T10:05:00",
        },
    ]
    CONTAINER.runtime_store.append("execution_fills", fills)
    truth = TruthEngine()
    truth.upsert_market_prices(
        [
            {
                "symbol": "BTCUSDT",
                "bid": 65990.0,
                "ask": 66010.0,
                "mid": 66000.0,
                "last": 66000.0,
                "mark_price": 66000.0,
                "source": "test",
                "quote_time": "2026-03-28T10:10:00",
                "stale": False,
            },
            {
                "symbol": "ETHUSDT",
                "bid": 2049.0,
                "ask": 2051.0,
                "mid": 2050.0,
                "last": 2050.0,
                "mark_price": 2050.0,
                "source": "test",
                "quote_time": "2026-03-28T10:10:00",
                "stale": False,
            },
            {
                "symbol": "DOGEUSDT",
                "bid": 0.0949,
                "ask": 0.0951,
                "mid": 0.095,
                "last": 0.095,
                "mark_price": 0.095,
                "source": "test",
                "quote_time": "2026-03-28T10:10:00",
                "stale": False,
            },
        ],
        "2026-03-28T10:10:00",
    )


def _normalize_positions(rows: list[dict]) -> list[dict]:
    normalized = []
    for row in rows:
        normalized.append(
            {
                "symbol": row["symbol"],
                "strategy_id": row["strategy_id"],
                "alpha_family": row["alpha_family"],
                "signed_qty": round(float(row["signed_qty"]), 8),
                "avg_entry_price": round(float(row["avg_entry_price"]), 8),
                "mark_price": round(float(row["mark_price"]), 8),
                "market_value": round(float(row["market_value"]), 8),
                "unrealized_pnl": round(float(row["unrealized_pnl"]), 8),
                "realized_pnl": round(float(row["realized_pnl"]), 8),
            }
        )
    return sorted(normalized, key=lambda row: (row["symbol"], row["strategy_id"], row["alpha_family"]))


def _latest_positions() -> list[dict]:
    return CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT snapshot_version, symbol, strategy_id, alpha_family, signed_qty, avg_entry_price,
               mark_price, market_value, unrealized_pnl, realized_pnl
        FROM position_snapshots_latest
        ORDER BY symbol, strategy_id, alpha_family
        """
    )


def _latest_equity() -> dict:
    row = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT cash_balance, used_margin, market_value, unrealized_pnl, realized_pnl,
               total_equity, available_margin, gross_exposure, net_exposure
        FROM equity_snapshots
        ORDER BY snapshot_time DESC
        LIMIT 1
        """
    )
    assert row is not None
    return {key: round(float(value), 8) for key, value in row.items()}


def test_incremental_latest_matches_full_rebuild_from_all_fills() -> None:
    _reset_runtime_state()
    truth = TruthEngine()
    truth.ensure_schema()
    truth.ensure_initial_capital()
    _seed_truth_inputs()

    positions_1 = truth.rebuild_positions("2026-03-28T10:03:30")
    truth.compute_equity_snapshot(positions_1, "2026-03-28T10:03:30")
    positions_2 = truth.rebuild_positions("2026-03-28T10:10:00")
    truth.compute_equity_snapshot(positions_2, "2026-03-28T10:10:00")

    incremental_positions = _normalize_positions(_latest_positions())
    incremental_equity = _latest_equity()

    CONTAINER.runtime_store.execute("DELETE FROM position_snapshots_latest")
    CONTAINER.runtime_store.execute("DELETE FROM position_snapshots_history")
    CONTAINER.runtime_store.execute("DELETE FROM position_snapshot_versions")
    CONTAINER.runtime_store.execute("DELETE FROM equity_snapshots")
    CONTAINER.runtime_store.execute("DELETE FROM truth_engine_state")

    rebuilt_positions = truth.rebuild_positions("2026-03-28T10:10:00")
    rebuilt_equity = truth.compute_equity_snapshot(rebuilt_positions, "2026-03-28T10:10:00")

    assert truth.last_rebuild_positions_metrics["rebuild_mode"] == "full"
    assert _normalize_positions(_latest_positions()) == incremental_positions
    assert _latest_equity() == incremental_equity
    assert round(float(rebuilt_equity["total_equity"]), 8) == incremental_equity["total_equity"]


def test_replay_rebuild_reproduces_truth_after_snapshot_reset() -> None:
    _reset_runtime_state()
    truth = TruthEngine()
    truth.ensure_schema()
    truth.ensure_initial_capital()
    _seed_truth_inputs()

    positions = truth.rebuild_positions("2026-03-28T10:10:00")
    equity = truth.compute_equity_snapshot(positions, "2026-03-28T10:10:00")
    original_positions = _normalize_positions(_latest_positions())
    original_equity = _latest_equity()

    CONTAINER.runtime_store.execute("DELETE FROM position_snapshots_latest")
    CONTAINER.runtime_store.execute("DELETE FROM position_snapshots_history")
    CONTAINER.runtime_store.execute("DELETE FROM position_snapshot_versions")
    CONTAINER.runtime_store.execute("DELETE FROM equity_snapshots")
    CONTAINER.runtime_store.execute("DELETE FROM truth_engine_state")

    replay_truth = TruthEngine()
    replay_truth.ensure_schema()
    replay_positions = replay_truth.rebuild_positions("2026-03-28T10:10:00")
    replay_equity = replay_truth.compute_equity_snapshot(replay_positions, "2026-03-28T10:10:00")

    assert replay_truth.last_rebuild_positions_metrics["full_rebuild_reason"] == "missing_active_snapshot"
    assert _normalize_positions(_latest_positions()) == original_positions
    assert _latest_equity() == original_equity
    assert round(float(replay_equity["total_equity"]), 8) == round(float(equity["total_equity"]), 8)
