from __future__ import annotations

from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app
from ai_hedge_bot.services.self_improving_service import SelfImprovingService


client = TestClient(app)


def _reset_phase7_state() -> None:
    for table in [
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
