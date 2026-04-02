from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
V12_APP = REPO_ROOT / "apps" / "v12-api"
if str(V12_APP) not in sys.path:
    sys.path.insert(0, str(V12_APP))

from fastapi.testclient import TestClient  # noqa: E402

from ai_hedge_bot.app.container import CONTAINER  # noqa: E402
from ai_hedge_bot.app.main import app  # noqa: E402


client = TestClient(app)


RESET_TABLES = [
    "audit_logs",
    "experiment_tracker",
    "validation_registry",
    "model_registry",
    "model_state_transitions",
    "model_live_reviews",
    "alpha_registry",
    "alpha_library",
    "alpha_status_events",
    "alpha_promotions",
    "alpha_demotions",
    "promotion_evaluations",
    "alpha_drift_events",
    "rollback_events",
    "champion_challenger_runs",
    "dataset_registry",
    "feature_registry",
]


def _reset_state() -> None:
    for table in RESET_TABLES:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def _decode_payload(row: dict[str, Any]) -> dict[str, Any]:
    try:
        return json.loads(str(row.get("payload_json") or "{}"))
    except Exception:
        return {}


def _audit_rows() -> list[dict[str, Any]]:
    rows = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT event_type, actor, payload_json
        FROM audit_logs
        WHERE category = 'research_factory'
        ORDER BY created_at ASC
        """
    )
    return [{"event_type": row["event_type"], "actor": row["actor"], "payload": _decode_payload(row)} for row in rows]


def _prepare_candidate(actor: str) -> str:
    client.post(
        "/research-factory/datasets/register",
        json={
            "dataset_id": "ds_gov",
            "dataset_version": "dataset.gov.v1",
            "source": actor,
            "created_by": actor,
            "actor": actor,
        },
    )
    client.post(
        "/research-factory/features/register",
        json={
            "feature_id": "feat_gov",
            "feature_version": "features.gov.v1",
            "feature_list": ["momentum_8", "oi_delta"],
            "created_by": actor,
            "actor": actor,
        },
    )
    client.post(
        "/alpha/generate",
        json={
            "alpha_id": "alpha.gov.mirror",
            "alpha_family": "derivatives",
            "factor_type": "carry",
            "feature_dependencies": ["funding_rate", "oi_delta"],
        },
    )
    experiment = client.post(
        "/research-factory/experiments/register",
        json={
            "experiment_id": "exp_gov",
            "dataset_version": "dataset.gov.v1",
            "feature_version": "features.gov.v1",
            "model_version": "model.gov.v1",
            "alpha_id": "alpha.gov.mirror",
            "strategy_id": "trend_core",
            "actor": actor,
        },
    ).json()
    exp_id = experiment["experiment"]["experiment_id"]
    client.post(
        "/research-factory/validations/register",
        json={
            "validation_id": "val_gov",
            "experiment_id": exp_id,
            "summary_score": 0.84,
            "passed": True,
            "actor": actor,
        },
    )
    model = client.post(
        "/research-factory/models/register",
        json={
            "model_id": "model_gov",
            "experiment_id": exp_id,
            "dataset_version": "dataset.gov.v1",
            "feature_version": "features.gov.v1",
            "model_version": "model.gov.v1",
            "validation_metrics": {"summary_score": 0.84, "max_drawdown": 0.08},
            "state": "candidate",
            "actor": actor,
        },
    ).json()
    return model["model"]["model_id"]


def verify() -> dict[str, Any]:
    failures: list[str] = []
    actor = "verify_research_governance_audit_mirroring"

    _reset_state()
    model_id = _prepare_candidate(actor)

    promotion = client.post(
        "/research-factory/promotion/evaluate",
        json={
            "model_id": model_id,
            "sample_size": 180,
            "regime_coverage": 0.86,
            "promotion_score_min": 0.75,
            "actor": actor,
        },
    )
    live_review = client.get("/research-factory/live-review")
    decay = client.get("/research-factory/alpha-decay")
    rollback = client.post(
        "/research-factory/rollback/evaluate",
        json={"model_id": model_id, "actor": actor},
    )
    cc = client.post(
        "/research-factory/champion-challenger/run",
        json={"actor": actor},
    )

    responses = {
        "promotion": promotion,
        "live_review": live_review,
        "decay": decay,
        "rollback": rollback,
        "champion_challenger": cc,
    }
    for name, response in responses.items():
        if response.status_code != 200:
            failures.append(f"{name} endpoint failed with status {response.status_code}")

    promotion_body = promotion.json() if promotion.status_code == 200 else {}
    live_review_body = live_review.json() if live_review.status_code == 200 else {}
    decay_body = decay.json() if decay.status_code == 200 else {}
    rollback_body = rollback.json() if rollback.status_code == 200 else {}
    cc_body = cc.json() if cc.status_code == 200 else {}

    promotion_row = CONTAINER.runtime_store.fetchone_dict(
        "SELECT evaluation_id, model_id, decision FROM promotion_evaluations ORDER BY created_at DESC LIMIT 1"
    )
    live_review_row = (live_review_body or {}).get("review")
    decay_row = CONTAINER.runtime_store.fetchone_dict(
        "SELECT event_id, model_id, alpha_id, severity, status FROM alpha_drift_events ORDER BY created_at DESC LIMIT 1"
    )
    rollback_row = CONTAINER.runtime_store.fetchone_dict(
        "SELECT rollback_id, model_id, action, trigger_reason FROM rollback_events ORDER BY created_at DESC LIMIT 1"
    )
    cc_row = CONTAINER.runtime_store.fetchone_dict(
        "SELECT run_id, champion_model_id, challenger_model_id, winner, recommended_action FROM champion_challenger_runs ORDER BY created_at DESC LIMIT 1"
    )

    audit_rows = _audit_rows()
    expected_governance_events = [
        "promotion_evaluated",
        "live_review_evaluated",
        "alpha_decay_evaluated",
        "rollback_evaluated",
        "champion_challenger_run",
    ]
    governance_rows = [row for row in audit_rows if row["event_type"] in expected_governance_events]
    by_event = {str(row["event_type"]): row for row in governance_rows}

    if [str(row["event_type"]) for row in governance_rows] != expected_governance_events:
        failures.append("expected governance audit events in promotion->live_review->alpha_decay->rollback->champion_challenger order")
    if any(str(row["actor"]) != actor for row in governance_rows if row["event_type"] != "live_review_evaluated" and row["event_type"] != "alpha_decay_evaluated"):
        failures.append("expected posted governance audit rows to preserve actor attribution")

    promotion_payload = (by_event.get("promotion_evaluated") or {}).get("payload", {})
    if str((promotion_row or {}).get("evaluation_id")) != str(promotion_payload.get("evaluation_id")):
        failures.append("promotion audit payload missing expected evaluation_id")
    if str(promotion_payload.get("model_id")) != model_id:
        failures.append("promotion audit payload missing expected model_id")

    live_review_payload = (by_event.get("live_review_evaluated") or {}).get("payload", {})
    if str((live_review_row or {}).get("review_id")) != str(live_review_payload.get("review_id")):
        failures.append("live_review audit payload missing expected review_id")
    if str(live_review_payload.get("model_id")) != str((live_review_row or {}).get("model_id")):
        failures.append("live_review audit payload missing expected model_id")

    decay_payload = (by_event.get("alpha_decay_evaluated") or {}).get("payload", {})
    if str((decay_row or {}).get("event_id")) != str(decay_payload.get("event_id")):
        failures.append("alpha_decay audit payload missing expected event_id")
    if str(decay_payload.get("alpha_id")) != str((decay_row or {}).get("alpha_id")):
        failures.append("alpha_decay audit payload missing expected alpha_id")

    rollback_payload = (by_event.get("rollback_evaluated") or {}).get("payload", {})
    if str((rollback_row or {}).get("rollback_id")) != str(rollback_payload.get("rollback_id")):
        failures.append("rollback audit payload missing expected rollback_id")
    if str(rollback_payload.get("model_id")) != model_id:
        failures.append("rollback audit payload missing expected model_id")

    cc_payload = (by_event.get("champion_challenger_run") or {}).get("payload", {})
    if str((cc_row or {}).get("run_id")) != str(cc_payload.get("run_id")):
        failures.append("champion_challenger audit payload missing expected run_id")
    if str(cc_payload.get("winner")) not in {"champion", "challenger"}:
        failures.append("champion_challenger audit payload missing expected winner")

    return {
        "status": "ok" if not failures else "failed",
        "lane": "audit_governance_mirroring",
        "governance_audit_rows": governance_rows,
        "canonical_rows": {
            "promotion": promotion_row,
            "live_review": live_review_row,
            "decay": decay_row,
            "rollback": rollback_row,
            "champion_challenger": cc_row,
        },
        "responses": {
            "promotion": promotion_body,
            "live_review": live_review_body,
            "decay": decay_body,
            "rollback": rollback_body,
            "champion_challenger": cc_body,
        },
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify research-factory governance decisions are mirrored into audit_logs.")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    try:
        result = verify()
    except Exception as exc:
        print(f"Verification failed unexpectedly: {exc}", file=sys.stderr)
        return 3

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status={result['status']} lane={result['lane']}")
        print(f"governance_audit_event_count={len(result['governance_audit_rows'])}")
        if result["failures"]:
            print("failures:")
            for failure in result["failures"]:
                print(f"- {failure}")

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
