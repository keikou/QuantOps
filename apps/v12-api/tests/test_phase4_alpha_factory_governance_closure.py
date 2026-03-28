from __future__ import annotations

from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app


client = TestClient(app)


def _reset_phase4_governance_state() -> None:
    for table in [
        "strategy_performance_daily",
        "execution_quality_snapshots",
        "experiment_tracker",
        "validation_registry",
        "model_registry",
        "model_state_transitions",
        "promotion_evaluations",
        "model_live_reviews",
        "alpha_drift_events",
        "rollback_events",
        "alpha_registry",
        "alpha_status_events",
        "alpha_promotions",
        "alpha_demotions",
        "alpha_rankings",
        "alpha_library",
    ]:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def test_phase4_runtime_result_drives_governance_state_transition() -> None:
    _reset_phase4_governance_state()

    alpha = client.post(
        "/alpha/generate",
        json={
            "alpha_id": "alpha.phase4.governance",
            "alpha_family": "derivatives",
            "factor_type": "carry",
            "feature_dependencies": ["funding_rate", "oi_delta"],
        },
    )
    assert alpha.status_code == 200
    alpha_id = alpha.json()["alpha"]["alpha_id"]

    experiment = client.post(
        "/research-factory/experiments/register",
        json={
            "experiment_id": "exp_phase4_governance",
            "dataset_version": "dataset.phase4.v1",
            "feature_version": "features.phase4.v1",
            "model_version": "model.phase4.v1",
            "alpha_id": alpha_id,
            "strategy_id": "trend_core",
        },
    )
    assert experiment.status_code == 200

    validation = client.post(
        "/research-factory/validations/register",
        json={"experiment_id": "exp_phase4_governance", "summary_score": 0.86, "passed": True},
    )
    assert validation.status_code == 200

    model = client.post(
        "/research-factory/models/register",
        json={
            "model_id": "model_phase4_governance",
            "experiment_id": "exp_phase4_governance",
            "dataset_version": "dataset.phase4.v1",
            "feature_version": "features.phase4.v1",
            "model_version": "model.phase4.v1",
            "validation_metrics": {"summary_score": 0.86, "max_drawdown": 0.07},
            "state": "live",
        },
    )
    assert model.status_code == 200
    model_id = model.json()["model"]["model_id"]

    promotion = client.post(
        "/research-factory/promotion/evaluate",
        json={"model_id": model_id, "sample_size": 240, "regime_coverage": 0.89},
    )
    assert promotion.status_code == 200
    assert promotion.json()["promotion"]["decision"] == "approve"

    CONTAINER.runtime_store.append(
        "strategy_performance_daily",
        {
            "perf_id": "perf_phase4_bad",
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
            "snapshot_id": "eqs_phase4_bad",
            "created_at": "2026-03-29T12:00:00+00:00",
            "run_id": "run_phase4_bad",
            "cycle_id": "cycle_phase4_bad",
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
    review_body = review.json()["review"]
    assert review_body["decision"] == "rollback"

    decay = client.get("/research-factory/alpha-decay")
    assert decay.status_code == 200
    decay_body = decay.json()["decay"]
    assert decay_body["status"] == "review_required"

    rollback = client.post("/research-factory/rollback/evaluate", json={"model_id": model_id})
    assert rollback.status_code == 200
    rollback_body = rollback.json()["rollback"]
    assert rollback_body["action"] == "rollback"

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
    latest_alpha_library = CONTAINER.runtime_store.fetchone_dict(
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
    latest_alpha_demotion = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT decision, source_run_id, notes
        FROM alpha_demotions
        WHERE alpha_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [alpha_id],
    )

    assert latest_model is not None
    assert latest_model["state"] == "rolled_back"
    assert latest_transition is not None
    assert latest_transition["to_state"] == "rolled_back"
    assert latest_transition["reason"] == "rollback_policy_triggered"

    assert latest_alpha_library is not None
    assert latest_alpha_library["state"] == "retired"
    assert latest_alpha_event is not None
    assert latest_alpha_event["event_type"] == "rollback"
    assert latest_alpha_event["to_state"] == "retired"
    assert latest_alpha_event["reason"] == "rollback_policy_triggered"

    assert latest_alpha_demotion is not None
    assert latest_alpha_demotion["decision"] == "rollback"
    assert str(latest_alpha_demotion["source_run_id"]).startswith("rollback_")
