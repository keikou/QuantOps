from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app
from ai_hedge_bot.signal import signal_service as signal_service_module


client = TestClient(app)


class _FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        fixed = datetime(2026, 3, 29, 10, 15, tzinfo=timezone.utc)
        if tz is None:
            return fixed.replace(tzinfo=None)
        return fixed.astimezone(tz)


def _reset_phase4_state() -> None:
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
        "alpha_registry",
        "alpha_experiments",
        "alpha_eval_results",
        "alpha_status_events",
        "alpha_promotions",
        "alpha_demotions",
        "alpha_rankings",
        "alpha_library",
        "dataset_registry",
        "feature_registry",
        "experiment_tracker",
        "validation_registry",
        "model_registry",
        "model_transitions",
        "promotion_evaluations",
        "live_model_reviews",
        "alpha_decay_events",
        "rollback_evaluations",
        "champion_challenger_runs",
    ]:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


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


def test_phase4_promoted_alpha_changes_runtime_portfolio_inclusion_and_execution() -> None:
    _reset_phase4_state()
    client.post("/runtime/resume")

    original_datetime = signal_service_module.datetime
    signal_service_module.datetime = _FixedDateTime
    try:
        baseline = client.post("/runtime/run-once?mode=paper")
        assert baseline.status_code == 200
        baseline_payload = baseline.json()
        assert baseline_payload["status"] == "ok"
        baseline_run_id = baseline_payload["run_id"]
        baseline_created_at = baseline_payload["result"]["timestamp"]

        baseline_signals = CONTAINER.runtime_store.fetchall_dict(
            """
            SELECT symbol, score, dominant_alpha
            FROM signals
            WHERE created_at = ?
            ORDER BY symbol ASC
            """,
            [baseline_created_at],
        )
        baseline_decisions = _decision_weights(baseline_created_at)
        baseline_plans = _plan_rows(baseline_run_id)
        baseline_plan_weights = {str(row["symbol"]): abs(float(row["target_weight"] or 0.0)) for row in baseline_plans}

        generated = client.post(
            "/alpha/generate",
            json={
                "alpha_family": "derivatives",
                "factor_type": "carry",
                "feature_dependencies": ["funding_rate", "oi_delta"],
                "turnover_profile": "medium",
            },
        )
        assert generated.status_code == 200
        alpha_id = generated.json()["alpha"]["alpha_id"]

        tested = client.post("/alpha/test", json={"alpha_id": alpha_id, "signal_strength": 0.95})
        assert tested.status_code == 200
        ranked = client.post("/alpha/evaluate", json={"alpha_id": alpha_id})
        assert ranked.status_code == 200
        ranking_body = ranked.json()["ranking"]
        assert ranking_body["alpha_id"] == alpha_id
        assert ranking_body["recommended_action"] == "promote"

        promoted = client.post("/runtime/run-once?mode=paper")
        assert promoted.status_code == 200
        promoted_payload = promoted.json()
        assert promoted_payload["status"] == "ok"
        promoted_run_id = promoted_payload["run_id"]
        promoted_created_at = promoted_payload["result"]["timestamp"]

        promoted_signals = CONTAINER.runtime_store.fetchall_dict(
            """
            SELECT symbol, score, dominant_alpha
            FROM signals
            WHERE created_at = ?
            ORDER BY symbol ASC
            """,
            [promoted_created_at],
        )
        promoted_decisions = _decision_weights(promoted_created_at)
        promoted_plans = _plan_rows(promoted_run_id)
        promoted_plan_weights = {str(row["symbol"]): abs(float(row["target_weight"] or 0.0)) for row in promoted_plans}
    finally:
        signal_service_module.datetime = original_datetime

    baseline_signal_map = {str(row["symbol"]): row for row in baseline_signals}
    promoted_signal_map = {str(row["symbol"]): row for row in promoted_signals}

    assert baseline_signal_map["BTCUSDT"]["dominant_alpha"] == "phase6_dynamic_alpha"
    assert promoted_signal_map["BTCUSDT"]["dominant_alpha"] == alpha_id
    assert float(promoted_signal_map["BTCUSDT"]["score"]) > float(baseline_signal_map["BTCUSDT"]["score"])

    assert promoted_decisions["BTCUSDT"] > baseline_decisions["BTCUSDT"]
    assert promoted_plan_weights["BTCUSDT"] > baseline_plan_weights["BTCUSDT"]
    assert any(str(row["symbol"]) == "BTCUSDT" for row in promoted_plans)
