from __future__ import annotations

from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app
from ai_hedge_bot.services.self_improving_service import SelfImprovingService
from ai_hedge_bot.signal import signal_service as signal_service_module
from ai_hedge_bot.api.routes import runtime as runtime_routes
from datetime import datetime, timezone


client = TestClient(app)


def _reset_phase7_state() -> None:
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
        "experiment_tracker",
        "validation_registry",
        "model_registry",
        "model_state_transitions",
        "model_live_reviews",
        "alpha_registry",
        "alpha_status_events",
        "alpha_library",
        "alpha_promotions",
        "alpha_demotions",
    ]:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


class _FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        fixed = datetime(2026, 3, 29, 14, 15, tzinfo=timezone.utc)
        if tz is None:
            return fixed.replace(tzinfo=None)
        return fixed.astimezone(tz)


def _register_phase7_model(alpha_id: str, model_id: str) -> None:
    alpha = client.post(
        "/alpha/generate",
        json={
            "alpha_id": alpha_id,
            "alpha_family": "derivatives",
            "factor_type": "carry",
            "feature_dependencies": ["funding_rate", "oi_delta"],
        },
    )
    assert alpha.status_code == 200

    experiment = client.post(
        "/research-factory/experiments/register",
        json={
            "experiment_id": f"exp_{alpha_id}",
            "dataset_version": "dataset.phase7.v1",
            "feature_version": "features.phase7.v1",
            "model_version": "model.phase7.v1",
            "alpha_id": alpha_id,
            "strategy_id": "trend_core",
        },
    )
    assert experiment.status_code == 200

    validation = client.post(
        "/research-factory/validations/register",
        json={"experiment_id": f"exp_{alpha_id}", "summary_score": 0.84, "passed": True},
    )
    assert validation.status_code == 200

    model = client.post(
        "/research-factory/models/register",
        json={
            "model_id": model_id,
            "experiment_id": f"exp_{alpha_id}",
            "dataset_version": "dataset.phase7.v1",
            "feature_version": "features.phase7.v1",
            "model_version": "model.phase7.v1",
            "validation_metrics": {"summary_score": 0.84, "max_drawdown": 0.06},
            "state": "live",
        },
    )
    assert model.status_code == 200


def _capture_phase7_outcome(model_id: str, alpha_id: str) -> dict:
    review = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT decision, pnl_drift, hit_rate, slippage_bps, fill_rate, turnover, risk_usage, flags_json
        FROM model_live_reviews
        WHERE model_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [model_id],
    )
    latest_model = CONTAINER.runtime_store.fetchone_dict(
        "SELECT state, notes FROM model_registry WHERE model_id = ? ORDER BY created_at DESC LIMIT 1",
        [model_id],
    )
    latest_transition = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT from_state, to_state, reason
        FROM model_state_transitions
        WHERE model_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [model_id],
    )
    latest_alpha = CONTAINER.runtime_store.fetchone_dict(
        "SELECT state FROM alpha_library WHERE alpha_id = ? ORDER BY created_at DESC LIMIT 1",
        [alpha_id],
    )
    latest_alpha_event = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT event_type, from_state, to_state, reason
        FROM alpha_status_events
        WHERE alpha_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [alpha_id],
    )
    return {
        "review": review,
        "latest_model": latest_model,
        "latest_transition": latest_transition,
        "latest_alpha": latest_alpha,
        "latest_alpha_event": latest_alpha_event,
    }


def test_phase7_close1_same_result_evidence_yields_same_governed_improvement_decision() -> None:
    evidence = {
        "created_at": "2026-03-29T14:00:00+00:00",
        "strategy_id": "trend_core",
        "expected_return": 0.11,
        "realized_return": 0.02,
        "hit_rate": 0.46,
        "turnover": 0.41,
        "drawdown": -0.09,
        "slippage_bps": 8.0,
        "fill_rate": 0.71,
        "risk_usage": 0.58,
    }

    outcomes: list[dict] = []
    for suffix in ("a", "b"):
        _reset_phase7_state()
        alpha_id = f"alpha.phase7.{suffix}"
        model_id = f"model_phase7_{suffix}"
        _register_phase7_model(alpha_id, model_id)

        service = SelfImprovingService()
        result = service.evaluate_result_evidence({**evidence, "model_id": model_id})
        assert result["status"] == "ok"
        assert result["decision"] == "reduce_capital"

        outcomes.append(
            {
                "result": result,
                "artifacts": _capture_phase7_outcome(model_id, alpha_id),
            }
        )

    first = outcomes[0]
    second = outcomes[1]

    assert first["result"]["decision"] == second["result"]["decision"] == "reduce_capital"
    assert first["result"]["flags"] == second["result"]["flags"] == ["pnl_drift", "fill_rate_weak", "hit_rate_weak"]
    assert first["artifacts"]["review"]["decision"] == second["artifacts"]["review"]["decision"] == "reduce_capital"
    assert first["artifacts"]["latest_model"]["state"] == second["artifacts"]["latest_model"]["state"] == "approved"
    assert first["artifacts"]["latest_transition"]["to_state"] == second["artifacts"]["latest_transition"]["to_state"] == "approved"
    assert first["artifacts"]["latest_transition"]["reason"] == second["artifacts"]["latest_transition"]["reason"] == "self_improving_reduce_capital"
    assert first["artifacts"]["latest_alpha"]["state"] == second["artifacts"]["latest_alpha"]["state"] == "monitor"
    assert first["artifacts"]["latest_alpha_event"]["to_state"] == second["artifacts"]["latest_alpha_event"]["to_state"] == "monitor"
    assert first["artifacts"]["latest_alpha_event"]["reason"] == second["artifacts"]["latest_alpha_event"]["reason"] == "self_improving_reduce_capital"


def test_phase7_close2_governed_improvement_decision_changes_next_cycle_runtime_state() -> None:
    _reset_phase7_state()
    client.post("/runtime/resume")

    alpha_id = "alpha.phase7.close2"
    model_id = "model_phase7_close2"
    _register_phase7_model(alpha_id, model_id)

    original_datetime = signal_service_module.datetime
    signal_service_module.datetime = _FixedDateTime
    try:
        baseline = client.post("/runtime/run-once?mode=paper")
        assert baseline.status_code == 200
        baseline_payload = baseline.json()
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
        baseline_plans = CONTAINER.runtime_store.fetchall_dict(
            """
            SELECT symbol, target_weight
            FROM execution_plans
            WHERE run_id = ?
            ORDER BY symbol ASC
            """,
            [baseline_run_id],
        )

        service = SelfImprovingService()
        deployed = service.evaluate_result_evidence(
            {
                "created_at": "2026-03-29T14:20:00+00:00",
                "model_id": model_id,
                "strategy_id": "trend_core",
                "expected_return": 0.12,
                "realized_return": 0.11,
                "hit_rate": 0.68,
                "turnover": 0.32,
                "drawdown": -0.05,
                "slippage_bps": 4.0,
                "fill_rate": 0.91,
                "risk_usage": 0.52,
            }
        )
        assert deployed["decision"] == "keep"

        promoted_row = CONTAINER.runtime_store.fetchone_dict(
            "SELECT decision, source_run_id FROM alpha_promotions WHERE alpha_id = ? ORDER BY created_at DESC LIMIT 1",
            [alpha_id],
        )
        ranking_row = CONTAINER.runtime_store.fetchone_dict(
            "SELECT recommended_action, rank_score FROM alpha_rankings WHERE alpha_id = ? ORDER BY created_at DESC LIMIT 1",
            [alpha_id],
        )
        assert promoted_row is not None
        assert promoted_row["decision"] == "promote"
        assert ranking_row is not None
        assert ranking_row["recommended_action"] == "promote"

        promoted = client.post("/runtime/run-once?mode=paper")
        assert promoted.status_code == 200
        promoted_payload = promoted.json()
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
        promoted_plans = CONTAINER.runtime_store.fetchall_dict(
            """
            SELECT symbol, target_weight
            FROM execution_plans
            WHERE run_id = ?
            ORDER BY symbol ASC
            """,
            [promoted_run_id],
        )
    finally:
        signal_service_module.datetime = original_datetime

    baseline_signal_map = {str(row["symbol"]): row for row in baseline_signals}
    promoted_signal_map = {str(row["symbol"]): row for row in promoted_signals}
    baseline_plan_map = {str(row["symbol"]): abs(float(row["target_weight"] or 0.0)) for row in baseline_plans}
    promoted_plan_map = {str(row["symbol"]): abs(float(row["target_weight"] or 0.0)) for row in promoted_plans}

    assert baseline_signal_map["BTCUSDT"]["dominant_alpha"] == "phase6_dynamic_alpha"
    assert promoted_signal_map["BTCUSDT"]["dominant_alpha"] == alpha_id
    assert float(promoted_signal_map["BTCUSDT"]["score"]) > float(baseline_signal_map["BTCUSDT"]["score"])
    assert promoted_plan_map["BTCUSDT"] > baseline_plan_map["BTCUSDT"]
