from fastapi.testclient import TestClient

from ai_hedge_bot.api.routes import runtime as runtime_routes
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app
from ai_hedge_bot.contracts.runtime_events import CYCLE_COMPLETED, FILL_RECORDED, ORDER_SUBMITTED, PORTFOLIO_UPDATED
from ai_hedge_bot.core.settings import SETTINGS
from ai_hedge_bot.portfolio.portfolio_service_phaseg import PhaseGPortfolioService


client = TestClient(app)


def _reset_runtime_state() -> None:
    for table in [
        "runtime_control_state",
        "runtime_runs",
        "runtime_run_steps",
        "scheduler_runs",
        "runtime_checkpoints",
        "runtime_events",
        "audit_logs",
        "signals",
        "signal_evaluations",
        "alpha_signal_snapshots",
        "alpha_candidates",
        "portfolio_signal_decisions",
        "portfolio_diagnostics",
        "portfolio_snapshots",
        "portfolio_positions",
        "rebalance_plans",
        "execution_plans",
        "execution_orders",
        "execution_fills",
        "execution_quality_snapshots",
        "execution_state_snapshots",
        "execution_block_reasons",
        "shadow_orders",
        "shadow_fills",
        "shadow_pnl_snapshots",
        "orchestrator_runs",
        "orchestrator_cycles",
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


def _signal(signal_id: str, symbol: str, score: float, side: str = "long") -> dict:
    return {
        "signal_id": signal_id,
        "symbol": symbol,
        "side": side,
        "score": score,
        "dominant_alpha": "phase3_test_alpha",
        "alpha_family": "phase3_test_family",
        "horizon": "intraday",
        "turnover_profile": "medium",
        "regime": "trend",
        "metadata": {},
    }


def _decision_weights(created_at: str) -> dict[str, float]:
    rows = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT symbol, target_weight
        FROM portfolio_signal_decisions
        WHERE created_at = ?
        ORDER BY symbol ASC
        """,
        [created_at],
    )
    return {str(row["symbol"]): float(row["target_weight"] or 0.0) for row in rows}


def _plan_rows(run_id: str) -> list[dict]:
    return CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT symbol, side, target_weight, order_qty
        FROM execution_plans
        WHERE run_id = ?
        ORDER BY symbol ASC
        """,
        [run_id],
    )


def _exposure_by_symbol(snapshot_time: str) -> dict[str, float]:
    rows = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT symbol, exposure_notional
        FROM position_snapshots_history
        WHERE snapshot_time = ?
        ORDER BY symbol ASC
        """,
        [snapshot_time],
    )
    return {str(row["symbol"]): float(row["exposure_notional"] or 0.0) for row in rows}


def test_phase3_score_weighted_allocation_changes_with_alpha_inputs() -> None:
    service = PhaseGPortfolioService()

    first = service.prepare(
        [
            _signal("sig-btc-high", "BTCUSDT", 0.92),
            _signal("sig-eth-mid", "ETHUSDT", 0.41),
            _signal("sig-sol-low", "SOLUSDT", 0.17),
            _signal("sig-wld-low", "WLDUSDT", 0.10),
            _signal("sig-doge-low", "DOGEUSDT", 0.06),
        ]
    )
    second = service.prepare(
        [
            _signal("sig-btc-low", "BTCUSDT", 0.18),
            _signal("sig-eth-high", "ETHUSDT", 0.88),
            _signal("sig-sol-mid", "SOLUSDT", 0.43),
            _signal("sig-wld-low", "WLDUSDT", 0.11),
            _signal("sig-doge-low", "DOGEUSDT", 0.07),
        ]
    )

    first_weights = {row["symbol"]: float(row["target_weight"]) for row in first["decisions"]}
    second_weights = {row["symbol"]: float(row["target_weight"]) for row in second["decisions"]}

    assert first["diagnostics"]["allocation_mode"] == "score_weighted"
    assert second["diagnostics"]["allocation_mode"] == "score_weighted"
    assert first["diagnostics"]["feedback_mode"] == "symbol_pnl_overlay"
    assert sum(first_weights.values()) <= SETTINGS.max_gross_exposure + 1e-6
    assert sum(second_weights.values()) <= SETTINGS.max_gross_exposure + 1e-6
    assert max(first_weights.values()) <= SETTINGS.max_symbol_weight + 1e-6
    assert max(second_weights.values()) <= SETTINGS.max_symbol_weight + 1e-6

    assert first_weights["BTCUSDT"] >= first_weights["ETHUSDT"] > first_weights["SOLUSDT"]
    assert second_weights["ETHUSDT"] >= second_weights["SOLUSDT"] > second_weights["BTCUSDT"]
    assert first_weights["BTCUSDT"] != second_weights["BTCUSDT"]
    assert first_weights["SOLUSDT"] != second_weights["SOLUSDT"]


def test_phase3_changed_alpha_inputs_rebalance_execution_and_positions() -> None:
    _reset_runtime_state()
    client.post("/runtime/resume")

    signal_sequences = [
        [
            _signal("run1-btc", "BTCUSDT", 0.95, side="long"),
            _signal("run1-eth", "ETHUSDT", 0.34, side="long"),
            _signal("run1-sol", "SOLUSDT", 0.22, side="long"),
            _signal("run1-wld", "WLDUSDT", 0.14, side="long"),
            _signal("run1-doge", "DOGEUSDT", 0.09, side="long"),
        ],
        [
            _signal("run2-btc", "BTCUSDT", 0.17, side="long"),
            _signal("run2-eth", "ETHUSDT", 0.91, side="long"),
            _signal("run2-sol", "SOLUSDT", 0.24, side="long"),
            _signal("run2-wld", "WLDUSDT", 0.13, side="long"),
            _signal("run2-doge", "DOGEUSDT", 0.08, side="long"),
        ],
    ]
    call_count = {"count": 0}

    def fake_generate(_symbols: list[str]) -> list[dict]:
        index = min(call_count["count"], len(signal_sequences) - 1)
        call_count["count"] += 1
        return signal_sequences[index]

    monkeypatch_target = runtime_routes._service.orchestrator._signal_service
    original_generate = monkeypatch_target.generate
    monkeypatch_target.generate = fake_generate
    try:
        first = client.post("/runtime/run-once?mode=paper")
        second = client.post("/runtime/run-once?mode=paper")
    finally:
        monkeypatch_target.generate = original_generate

    assert first.status_code == 200
    assert second.status_code == 200

    first_payload = first.json()
    second_payload = second.json()
    assert first_payload["status"] == "ok"
    assert second_payload["status"] == "ok"

    first_run_id = first_payload["run_id"]
    second_run_id = second_payload["run_id"]
    first_created_at = first_payload["result"]["timestamp"]
    second_created_at = second_payload["result"]["timestamp"]

    first_decisions = _decision_weights(first_created_at)
    second_decisions = _decision_weights(second_created_at)
    assert first_decisions["BTCUSDT"] > first_decisions["ETHUSDT"]
    assert second_decisions["ETHUSDT"] > second_decisions["BTCUSDT"]

    first_plans = _plan_rows(first_run_id)
    second_plans = _plan_rows(second_run_id)
    first_plan_weights = {str(row["symbol"]): abs(float(row["target_weight"] or 0.0)) for row in first_plans}
    second_plan_weights = {str(row["symbol"]): abs(float(row["target_weight"] or 0.0)) for row in second_plans}
    assert first_plan_weights["BTCUSDT"] > first_plan_weights["ETHUSDT"]
    assert second_plan_weights["ETHUSDT"] > second_plan_weights["BTCUSDT"]

    assert any(str(row["symbol"]) == "BTCUSDT" and str(row["side"]).lower() == "sell" for row in second_plans)
    assert any(str(row["symbol"]) == "ETHUSDT" and str(row["side"]).lower() == "buy" for row in second_plans)

    bridge = client.get(f"/execution/bridge/by-run/{second_run_id}")
    assert bridge.status_code == 200
    bridge_payload = bridge.json()
    assert bridge_payload["status"] == "ok"
    assert bridge_payload["event_chain_complete"] is True
    assert bridge_payload["bridge_state"] == "filled"

    events = client.get(f"/runtime/events/by-run/{second_run_id}?limit=200")
    assert events.status_code == 200
    event_types = {item["event_type"] for item in events.json()["items"]}
    assert {PORTFOLIO_UPDATED, ORDER_SUBMITTED, FILL_RECORDED, CYCLE_COMPLETED}.issubset(event_types)

    second_snapshot_rows = _exposure_by_symbol(second_created_at)
    assert "BTCUSDT" in second_snapshot_rows
    assert "ETHUSDT" in second_snapshot_rows

    rebalance_rows = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT run_id, action_count, gross_delta
        FROM rebalance_plans
        ORDER BY created_at DESC
        LIMIT 2
        """
    )
    assert any(str(row["run_id"]) == second_run_id for row in rebalance_rows)
    assert any(int(row["action_count"] or 0) >= 1 for row in rebalance_rows if str(row["run_id"]) == second_run_id)


def test_phase3_realized_result_changes_next_allocation_with_same_alpha_inputs() -> None:
    _reset_runtime_state()
    client.post("/runtime/resume")

    static_signals = [
        _signal("phase3-btc", "BTCUSDT", 0.76, side="long"),
        _signal("phase3-eth", "ETHUSDT", 0.52, side="long"),
        _signal("phase3-sol", "SOLUSDT", 0.23, side="long"),
        _signal("phase3-wld", "WLDUSDT", 0.14, side="long"),
        _signal("phase3-doge", "DOGEUSDT", 0.09, side="long"),
    ]

    def fake_generate(_symbols: list[str]) -> list[dict]:
        return list(static_signals)

    monkeypatch_target = runtime_routes._service.orchestrator._signal_service
    original_generate = monkeypatch_target.generate
    monkeypatch_target.generate = fake_generate
    try:
        first = client.post("/runtime/run-once?mode=paper")
        assert first.status_code == 200
        first_payload = first.json()
        assert first_payload["status"] == "ok"
        first_created_at = first_payload["result"]["timestamp"]
        first_weights = _decision_weights(first_created_at)
        assert first_weights["BTCUSDT"] > first_weights["ETHUSDT"]

        CONTAINER.runtime_store.execute(
            """
            UPDATE position_snapshots_latest
            SET realized_pnl = CASE
                    WHEN symbol = 'BTCUSDT' THEN -4000.0
                    WHEN symbol = 'ETHUSDT' THEN 1500.0
                    ELSE COALESCE(realized_pnl, 0.0)
                END,
                unrealized_pnl = CASE
                    WHEN symbol = 'BTCUSDT' THEN -2500.0
                    WHEN symbol = 'ETHUSDT' THEN 2200.0
                    ELSE COALESCE(unrealized_pnl, 0.0)
                END,
                exposure_notional = CASE
                    WHEN symbol IN ('BTCUSDT', 'ETHUSDT') THEN 10000.0
                    ELSE COALESCE(exposure_notional, 0.0)
                END
            WHERE symbol IN ('BTCUSDT', 'ETHUSDT')
            """
        )

        second = client.post("/runtime/run-once?mode=paper")
    finally:
        monkeypatch_target.generate = original_generate

    assert second.status_code == 200
    second_payload = second.json()
    assert second_payload["status"] == "ok"
    second_created_at = second_payload["result"]["timestamp"]
    second_run_id = second_payload["run_id"]

    second_weights = _decision_weights(second_created_at)
    assert second_weights["ETHUSDT"] > second_weights["BTCUSDT"]

    second_plans = _plan_rows(second_run_id)
    second_plan_weights = {str(row["symbol"]): abs(float(row["target_weight"] or 0.0)) for row in second_plans}
    assert second_plan_weights["ETHUSDT"] > second_plan_weights["BTCUSDT"]

    diagnostics = getattr(CONTAINER, "latest_portfolio_diagnostics", {}) or {}
    assert diagnostics.get("feedback_applied") is True
    assert "BTCUSDT" in diagnostics.get("feedback_symbols", [])
    assert "ETHUSDT" in diagnostics.get("feedback_symbols", [])
