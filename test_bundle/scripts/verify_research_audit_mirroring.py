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
    "dataset_registry",
    "feature_registry",
    "experiment_tracker",
    "validation_registry",
    "model_registry",
    "model_state_transitions",
]


def _reset_state() -> None:
    for table in RESET_TABLES:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def _audit_rows() -> list[dict[str, Any]]:
    return CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT event_type, actor, payload_json
        FROM audit_logs
        WHERE category = 'research_factory'
        ORDER BY created_at ASC
        """
    )


def _decode_payload(row: dict[str, Any]) -> dict[str, Any]:
    try:
        return json.loads(str(row.get("payload_json") or "{}"))
    except Exception:
        return {}


def verify() -> dict[str, Any]:
    failures: list[str] = []
    actor = "verify_research_audit_mirroring"

    _reset_state()

    dataset = client.post(
        "/research-factory/datasets/register",
        json={
            "dataset_id": "ds_mirror",
            "dataset_version": "dataset.mirror.v1",
            "source": "verify_research_audit_mirroring",
            "symbol_scope": ["BTCUSDT", "ETHUSDT"],
            "timeframe": "5m",
            "created_by": actor,
            "actor": actor,
        },
    )
    feature = client.post(
        "/research-factory/features/register",
        json={
            "feature_id": "feat_mirror",
            "feature_version": "features.mirror.v1",
            "feature_list": ["momentum_8", "oi_delta"],
            "created_by": actor,
            "actor": actor,
        },
    )
    experiment = client.post(
        "/research-factory/experiments/register",
        json={
            "experiment_id": "exp_mirror",
            "dataset_version": "dataset.mirror.v1",
            "feature_version": "features.mirror.v1",
            "model_version": "model.mirror.v1",
            "alpha_id": "alpha.mirror",
            "strategy_id": "trend_core",
            "actor": actor,
        },
    )
    validation = client.post(
        "/research-factory/validations/register",
        json={
            "validation_id": "val_mirror",
            "experiment_id": "exp_mirror",
            "summary_score": 0.83,
            "passed": True,
            "actor": actor,
        },
    )
    model = client.post(
        "/research-factory/models/register",
        json={
            "model_id": "model_mirror",
            "experiment_id": "exp_mirror",
            "dataset_version": "dataset.mirror.v1",
            "feature_version": "features.mirror.v1",
            "model_version": "model.mirror.v1",
            "state": "candidate",
            "actor": actor,
        },
    )

    responses = {
        "dataset": dataset,
        "feature": feature,
        "experiment": experiment,
        "validation": validation,
        "model": model,
    }
    for name, response in responses.items():
        if response.status_code != 200:
            failures.append(f"{name} registration failed with status {response.status_code}")

    dataset_row = CONTAINER.runtime_store.fetchone_dict(
        "SELECT dataset_id, dataset_version, created_by FROM dataset_registry WHERE dataset_id = 'ds_mirror' ORDER BY registered_at DESC LIMIT 1"
    )
    feature_row = CONTAINER.runtime_store.fetchone_dict(
        "SELECT feature_id, feature_version, created_by FROM feature_registry WHERE feature_id = 'feat_mirror' ORDER BY registered_at DESC LIMIT 1"
    )
    experiment_row = CONTAINER.runtime_store.fetchone_dict(
        "SELECT experiment_id, dataset_version, feature_version, model_version FROM experiment_tracker WHERE experiment_id = 'exp_mirror' ORDER BY created_at DESC LIMIT 1"
    )
    validation_row = CONTAINER.runtime_store.fetchone_dict(
        "SELECT validation_id, experiment_id, summary_score, passed FROM validation_registry WHERE validation_id = 'val_mirror' ORDER BY created_at DESC LIMIT 1"
    )
    model_row = CONTAINER.runtime_store.fetchone_dict(
        "SELECT model_id, experiment_id, dataset_version, feature_version, model_version, state FROM model_registry WHERE model_id = 'model_mirror' ORDER BY created_at DESC LIMIT 1"
    )

    audit_rows = _audit_rows()
    decoded = [{"event_type": row["event_type"], "actor": row["actor"], "payload": _decode_payload(row)} for row in audit_rows]
    by_event = {str(row["event_type"]): row for row in decoded}

    expected_events = [
        "dataset_registered",
        "feature_registered",
        "experiment_registered",
        "validation_registered",
        "model_registered",
    ]
    if [str(row["event_type"]) for row in decoded] != expected_events:
        failures.append("expected research_factory audit events in dataset->feature->experiment->validation->model order")
    if any(str(row["actor"]) != actor for row in decoded):
        failures.append("expected all mirrored research_factory audit rows to preserve actor attribution")

    if str((dataset_row or {}).get("dataset_version")) != "dataset.mirror.v1":
        failures.append("dataset canonical row missing expected dataset_version")
    if str((feature_row or {}).get("feature_version")) != "features.mirror.v1":
        failures.append("feature canonical row missing expected feature_version")
    if str((experiment_row or {}).get("experiment_id")) != "exp_mirror":
        failures.append("experiment canonical row missing expected experiment_id")
    if str((validation_row or {}).get("validation_id")) != "val_mirror":
        failures.append("validation canonical row missing expected validation_id")
    if str((model_row or {}).get("model_id")) != "model_mirror":
        failures.append("model canonical row missing expected model_id")

    dataset_payload = (by_event.get("dataset_registered") or {}).get("payload", {})
    if str(dataset_payload.get("dataset_id")) != "ds_mirror":
        failures.append("dataset audit payload missing expected dataset_id")
    if str(dataset_payload.get("dataset_version")) != "dataset.mirror.v1":
        failures.append("dataset audit payload missing expected dataset_version")

    feature_payload = (by_event.get("feature_registered") or {}).get("payload", {})
    if str(feature_payload.get("feature_id")) != "feat_mirror":
        failures.append("feature audit payload missing expected feature_id")
    if str(feature_payload.get("feature_version")) != "features.mirror.v1":
        failures.append("feature audit payload missing expected feature_version")
    if int(feature_payload.get("feature_count", 0) or 0) != 2:
        failures.append("feature audit payload missing expected feature_count")

    experiment_payload = (by_event.get("experiment_registered") or {}).get("payload", {})
    if str(experiment_payload.get("experiment_id")) != "exp_mirror":
        failures.append("experiment audit payload missing expected experiment_id")
    if str(experiment_payload.get("dataset_version")) != "dataset.mirror.v1":
        failures.append("experiment audit payload missing expected dataset_version")
    if str(experiment_payload.get("feature_version")) != "features.mirror.v1":
        failures.append("experiment audit payload missing expected feature_version")
    if bool(experiment_payload.get("immutable_record")) is not True:
        failures.append("experiment audit payload missing immutable_record=true")

    validation_payload = (by_event.get("validation_registered") or {}).get("payload", {})
    if str(validation_payload.get("validation_id")) != "val_mirror":
        failures.append("validation audit payload missing expected validation_id")
    if str(validation_payload.get("experiment_id")) != "exp_mirror":
        failures.append("validation audit payload missing expected experiment_id")
    if bool(validation_payload.get("passed")) is not True:
        failures.append("validation audit payload missing passed=true")

    model_payload = (by_event.get("model_registered") or {}).get("payload", {})
    if str(model_payload.get("model_id")) != "model_mirror":
        failures.append("model audit payload missing expected model_id")
    if str(model_payload.get("experiment_id")) != "exp_mirror":
        failures.append("model audit payload missing expected experiment_id")
    if str(model_payload.get("dataset_version")) != "dataset.mirror.v1":
        failures.append("model audit payload missing expected dataset_version")
    if str(model_payload.get("feature_version")) != "features.mirror.v1":
        failures.append("model audit payload missing expected feature_version")
    if str(model_payload.get("state")) != "candidate":
        failures.append("model audit payload missing expected state")

    return {
        "status": "ok" if not failures else "failed",
        "lane": "audit_provenance_mirroring",
        "audit_rows": decoded,
        "canonical_rows": {
            "dataset": dataset_row,
            "feature": feature_row,
            "experiment": experiment_row,
            "validation": validation_row,
            "model": model_row,
        },
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify research-factory registrations are mirrored into audit_logs.")
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
        print(f"audit_event_count={len(result['audit_rows'])}")
        if result["failures"]:
            print("failures:")
            for failure in result["failures"]:
                print(f"- {failure}")

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
