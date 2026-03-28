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


def _reset_phase4_close3_state() -> None:
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
        "strategy_performance_daily",
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
        "model_state_transitions",
        "promotion_evaluations",
        "model_live_reviews",
        "alpha_drift_events",
        "rollback_events",
        "champion_challenger_runs",
    ]:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def _latest_signal_map(created_at: str) -> dict[str, dict]:
    rows = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT symbol, score, dominant_alpha
        FROM signals
        WHERE created_at = ?
        ORDER BY symbol ASC
        """,
        [created_at],
    )
    return {str(row["symbol"]): row for row in rows}


def _plan_weight_map(run_id: str) -> dict[str, float]:
    rows = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT symbol, target_weight
        FROM execution_plans
        WHERE run_id = ?
        ORDER BY symbol ASC
        """,
        [run_id],
    )
    return {str(row["symbol"]): abs(float(row["target_weight"] or 0.0)) for row in rows}


def _register_promoted_alpha(alpha_id: str) -> str:
    client.post(
        "/alpha/generate",
        json={
            "alpha_id": alpha_id,
            "alpha_family": "derivatives",
            "factor_type": "carry",
            "feature_dependencies": ["funding_rate", "oi_delta"],
            "turnover_profile": "medium",
        },
    )
    client.post("/alpha/test", json={"alpha_id": alpha_id, "signal_strength": 0.95})
    client.post("/alpha/evaluate", json={"alpha_id": alpha_id})

    experiment = client.post(
        "/research-factory/experiments/register",
        json={
            "experiment_id": f"exp_{alpha_id}",
            "dataset_version": "dataset.phase4.v1",
            "feature_version": "features.phase4.v1",
            "model_version": "model.phase4.v1",
            "alpha_id": alpha_id,
            "strategy_id": "trend_core",
        },
    )
    assert experiment.status_code == 200
    client.post(
        "/research-factory/validations/register",
        json={"experiment_id": f"exp_{alpha_id}", "summary_score": 0.86, "passed": True},
    )
    model = client.post(
        "/research-factory/models/register",
        json={
            "model_id": f"model_{alpha_id}",
            "experiment_id": f"exp_{alpha_id}",
            "dataset_version": "dataset.phase4.v1",
            "feature_version": "features.phase4.v1",
            "model_version": "model.phase4.v1",
            "validation_metrics": {"summary_score": 0.86, "max_drawdown": 0.07},
            "state": "live",
        },
    )
    assert model.status_code == 200
    model_id = model.json()["model"]["model_id"]
    promoted = client.post(
        "/research-factory/promotion/evaluate",
        json={"model_id": model_id, "sample_size": 240, "regime_coverage": 0.89},
    )
    assert promoted.status_code == 200
    assert promoted.json()["promotion"]["decision"] == "approve"
    return model_id


def test_phase4_close3_persisted_governance_outcome_controls_next_cycle_reuse() -> None:
    _reset_phase4_close3_state()
    client.post("/runtime/resume")

    original_datetime = signal_service_module.datetime
    signal_service_module.datetime = _FixedDateTime
    try:
        baseline = client.post("/runtime/run-once?mode=paper")
        assert baseline.status_code == 200
        baseline_run_id = baseline.json()["run_id"]
        baseline_created_at = baseline.json()["result"]["timestamp"]

        alpha_id = "alpha.phase4.close3"
        model_id = _register_promoted_alpha(alpha_id)

        promoted = client.post("/runtime/run-once?mode=paper")
        assert promoted.status_code == 200
        promoted_run_id = promoted.json()["run_id"]
        promoted_created_at = promoted.json()["result"]["timestamp"]

        baseline_signal_map = _latest_signal_map(baseline_created_at)
        promoted_signal_map = _latest_signal_map(promoted_created_at)
        baseline_plan_map = _plan_weight_map(baseline_run_id)
        promoted_plan_map = _plan_weight_map(promoted_run_id)

        assert promoted_signal_map["BTCUSDT"]["dominant_alpha"] == alpha_id
        assert float(promoted_signal_map["BTCUSDT"]["score"]) > float(baseline_signal_map["BTCUSDT"]["score"])
        assert promoted_plan_map["BTCUSDT"] > baseline_plan_map["BTCUSDT"]

        CONTAINER.runtime_store.append(
            "strategy_performance_daily",
            {
                "perf_id": "perf_close3_bad",
                "created_at": "2026-03-29T12:00:00+00:00",
                "strategy_id": "trend_core",
                "strategy_name": "Trend Core",
                "capital_weight": 0.42,
                "expected_return": 0.12,
                "realized_return": -0.05,
                "hit_rate": 0.31,
                "turnover": 0.58,
                "cost_adjusted_score": 0.18,
                "drawdown": -0.19,
            },
        )
        CONTAINER.runtime_store.append(
            "execution_quality_snapshots",
            {
                "snapshot_id": "eqs_close3_bad",
                "created_at": "2026-03-29T12:00:00+00:00",
                "run_id": "run_close3_bad",
                "cycle_id": "cycle_close3_bad",
                "mode": "paper",
                "order_count": 6,
                "fill_count": 2,
                "fill_rate": 0.33,
                "avg_slippage_bps": 18.5,
                "latency_ms_p50": 1200.0,
                "latency_ms_p95": 2400.0,
            },
        )

        review = client.get("/research-factory/live-review")
        assert review.status_code == 200
        assert review.json()["review"]["decision"] == "rollback"
        rollback = client.post("/research-factory/rollback/evaluate", json={"model_id": model_id})
        assert rollback.status_code == 200
        assert rollback.json()["rollback"]["action"] == "rollback"

        next_cycle = client.post("/runtime/run-once?mode=paper")
        assert next_cycle.status_code == 200
        next_run_id = next_cycle.json()["run_id"]
        next_created_at = next_cycle.json()["result"]["timestamp"]
    finally:
        signal_service_module.datetime = original_datetime

    next_signal_map = _latest_signal_map(next_created_at)
    next_plan_map = _plan_weight_map(next_run_id)
    latest_alpha_library = CONTAINER.runtime_store.fetchone_dict(
        "SELECT state FROM alpha_library WHERE alpha_id = ? ORDER BY created_at DESC LIMIT 1",
        [alpha_id],
    )

    assert latest_alpha_library is not None
    assert latest_alpha_library["state"] == "retired"
    assert next_signal_map["BTCUSDT"]["dominant_alpha"] == "phase6_dynamic_alpha"
    assert float(next_signal_map["BTCUSDT"]["score"]) < float(promoted_signal_map["BTCUSDT"]["score"])
    assert next_plan_map["BTCUSDT"] < promoted_plan_map["BTCUSDT"]
    assert abs(next_plan_map["BTCUSDT"] - baseline_plan_map["BTCUSDT"]) < 1e-4
