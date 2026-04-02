from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
V12_APP = REPO_ROOT / "apps" / "v12-api"
if str(V12_APP) not in sys.path:
    sys.path.insert(0, str(V12_APP))

from fastapi.testclient import TestClient  # noqa: E402

from ai_hedge_bot.app.container import CONTAINER  # noqa: E402
from ai_hedge_bot.services.self_improving_service import SelfImprovingService  # noqa: E402
from ai_hedge_bot.services.runtime.runtime_service import RuntimeService  # noqa: E402
from ai_hedge_bot.signal import signal_service as signal_service_module  # noqa: E402
from ai_hedge_bot.app.main import app  # noqa: E402


client = TestClient(app)


RESET_TABLES = [
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
    "dataset_registry",
    "feature_registry",
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
    "alpha_rankings",
    "promotion_evaluations",
]


class _FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        fixed = datetime(2026, 4, 1, 9, 30, tzinfo=timezone.utc)
        if tz is None:
            return fixed.replace(tzinfo=None)
        return fixed.astimezone(tz)


def _reset_state() -> None:
    for table in RESET_TABLES:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def _register_research_lineage(alpha_id: str, experiment_id: str, model_id: str) -> dict[str, Any]:
    dataset = client.post(
        "/research-factory/datasets/register",
        json={
            "dataset_id": "ds_audit_prov",
            "dataset_version": "dataset.audit.v1",
            "source": "verify_audit_provenance",
            "symbol_scope": ["BTCUSDT", "ETHUSDT"],
            "timeframe": "5m",
            "missing_rate": 0.01,
            "created_by": "verify_audit_provenance",
        },
    )
    feature = client.post(
        "/research-factory/features/register",
        json={
            "feature_id": "feat_audit_prov",
            "feature_version": "features.audit.v1",
            "feature_list": ["momentum_8", "oi_delta", "funding_zscore"],
            "created_by": "verify_audit_provenance",
        },
    )
    alpha = client.post(
        "/alpha/generate",
        json={
            "alpha_id": alpha_id,
            "alpha_family": "derivatives",
            "factor_type": "carry",
            "feature_dependencies": ["funding_rate", "oi_delta"],
        },
    )
    experiment = client.post(
        "/research-factory/experiments/register",
        json={
            "experiment_id": experiment_id,
            "dataset_version": "dataset.audit.v1",
            "feature_version": "features.audit.v1",
            "model_version": "model.audit.v1",
            "alpha_id": alpha_id,
            "strategy_id": "trend_core",
            "notes": "verify_audit_provenance immutable experiment",
        },
    )
    validation = client.post(
        "/research-factory/validations/register",
        json={
            "experiment_id": experiment_id,
            "summary_score": 0.84,
            "passed": True,
        },
    )
    model = client.post(
        "/research-factory/models/register",
        json={
            "model_id": model_id,
            "experiment_id": experiment_id,
            "dataset_version": "dataset.audit.v1",
            "feature_version": "features.audit.v1",
            "model_version": "model.audit.v1",
            "validation_metrics": {"summary_score": 0.84, "max_drawdown": 0.06},
            "state": "live",
            "notes": "verify_audit_provenance model registration",
        },
    )
    responses = {
        "dataset": dataset,
        "feature": feature,
        "alpha": alpha,
        "experiment": experiment,
        "validation": validation,
        "model": model,
    }
    for name, response in responses.items():
        if response.status_code != 200:
            raise RuntimeError(f"{name} registration failed: {response.status_code} {response.text}")
    return {name: response.json() for name, response in responses.items()}


def _fetch_single(query: str, params: list[Any] | None = None) -> dict[str, Any] | None:
    return CONTAINER.runtime_store.fetchone_dict(query, params or [])


def _fetch_all(query: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
    return CONTAINER.runtime_store.fetchall_dict(query, params or [])


def _run_promoted_cycle(model_id: str, alpha_id: str) -> dict[str, Any]:
    runtime_service = RuntimeService()
    runtime_service.resume_trading("audit provenance baseline resume", actor="verify_audit_provenance")
    original_datetime = signal_service_module.datetime
    signal_service_module.datetime = _FixedDateTime
    try:
        baseline = runtime_service.run_once(mode="paper", job_name="audit_provenance_baseline", triggered_by="verify_audit_provenance")
        self_improving = SelfImprovingService().evaluate_result_evidence(
            {
                "created_at": "2026-04-01T14:05:00+00:00",
                "model_id": model_id,
                "strategy_id": "trend_core",
                "expected_return": 0.12,
                "realized_return": 0.11,
                "hit_rate": 0.69,
                "turnover": 0.31,
                "drawdown": -0.05,
                "slippage_bps": 4.0,
                "fill_rate": 0.92,
                "risk_usage": 0.51,
                "notes": "verify_audit_provenance governance linkage",
            }
        )
        promoted = runtime_service.run_once(mode="paper", job_name="audit_provenance_promoted", triggered_by="verify_audit_provenance")
        halted = runtime_service.halt_trading("audit provenance halt", actor="verify_audit_provenance")
        resumed = runtime_service.resume_trading("audit provenance resume", actor="verify_audit_provenance")
    finally:
        signal_service_module.datetime = original_datetime
    return {
        "baseline": baseline,
        "self_improving": self_improving,
        "promoted": promoted,
        "halted": halted,
        "resumed": resumed,
        "alpha_id": alpha_id,
    }


def verify() -> dict[str, Any]:
    failures: list[str] = []
    alpha_id = "alpha.audit.provenance"
    experiment_id = "exp_alpha_audit_provenance"
    model_id = "model_audit_provenance"

    _reset_state()
    registrations = _register_research_lineage(alpha_id, experiment_id, model_id)
    scenario = _run_promoted_cycle(model_id, alpha_id)

    baseline_run = scenario["baseline"]["run_id"]
    promoted_run = scenario["promoted"]["run_id"]
    promoted_ts = scenario["promoted"]["result"]["timestamp"]

    dataset_row = _fetch_single(
        """
        SELECT dataset_version, source, created_by
        FROM dataset_registry
        WHERE dataset_id = 'ds_audit_prov'
        ORDER BY registered_at DESC
        LIMIT 1
        """
    )
    feature_row = _fetch_single(
        """
        SELECT feature_version, created_by
        FROM feature_registry
        WHERE feature_id = 'feat_audit_prov'
        ORDER BY registered_at DESC
        LIMIT 1
        """
    )
    experiment_row = _fetch_single(
        """
        SELECT experiment_id, dataset_version, feature_version, model_version, alpha_id, strategy_id, immutable_record, notes
        FROM experiment_tracker
        WHERE experiment_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [experiment_id],
    )
    model_row = _fetch_single(
        """
        SELECT model_id, experiment_id, dataset_version, feature_version, model_version, state, notes
        FROM model_registry
        WHERE model_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [model_id],
    )
    latest_model_transition = _fetch_single(
        """
        SELECT from_state, to_state, reason
        FROM model_state_transitions
        WHERE model_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [model_id],
    )
    latest_alpha_event = _fetch_single(
        """
        SELECT event_type, from_state, to_state, reason
        FROM alpha_status_events
        WHERE alpha_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [alpha_id],
    )
    latest_alpha_library = _fetch_single(
        """
        SELECT state
        FROM alpha_library
        WHERE alpha_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [alpha_id],
    )
    latest_promotion = _fetch_single(
        """
        SELECT decision, source_run_id, notes
        FROM alpha_promotions
        WHERE alpha_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [alpha_id],
    )
    promoted_btc_signal = _fetch_single(
        """
        SELECT symbol, score, dominant_alpha
        FROM signals
        WHERE created_at = ? AND symbol = 'BTCUSDT'
        LIMIT 1
        """,
        [promoted_ts],
    )
    promoted_run_record = _fetch_single(
        """
        SELECT run_id, job_name, mode, status, triggered_by
        FROM runtime_runs
        WHERE run_id = ?
        LIMIT 1
        """,
        [promoted_run],
    )
    promoted_step = _fetch_single(
        """
        SELECT step_name, status
        FROM runtime_run_steps
        WHERE run_id = ?
        ORDER BY started_at ASC
        LIMIT 1
        """,
        [promoted_run],
    )
    promoted_checkpoint = _fetch_single(
        """
        SELECT checkpoint_name, payload_json
        FROM runtime_checkpoints
        WHERE run_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [promoted_run],
    )
    promoted_audit_logs = _fetch_all(
        """
        SELECT event_type, actor, payload_json
        FROM audit_logs
        WHERE run_id = ?
        ORDER BY created_at ASC
        """,
        [promoted_run],
    )
    guard_audit_logs = _fetch_all(
        """
        SELECT event_type, actor, payload_json
        FROM audit_logs
        WHERE category = 'runtime' AND run_id IS NULL
        ORDER BY created_at ASC
        """
    )

    if scenario["baseline"]["status"] != "ok":
        failures.append("baseline runtime cycle did not complete successfully")
    if scenario["promoted"]["status"] != "ok":
        failures.append("promoted runtime cycle did not complete successfully")
    if baseline_run == promoted_run:
        failures.append("baseline and promoted runtime runs should be distinct")
    if scenario["self_improving"]["decision"] != "keep":
        failures.append("expected self-improving decision keep for provenance scenario")

    if str((dataset_row or {}).get("dataset_version")) != "dataset.audit.v1":
        failures.append("dataset provenance row missing expected dataset_version")
    if str((dataset_row or {}).get("created_by")) != "verify_audit_provenance":
        failures.append("dataset provenance row missing created_by attribution")
    if str((feature_row or {}).get("feature_version")) != "features.audit.v1":
        failures.append("feature provenance row missing expected feature_version")
    if str((feature_row or {}).get("created_by")) != "verify_audit_provenance":
        failures.append("feature provenance row missing created_by attribution")

    if str((experiment_row or {}).get("experiment_id")) != experiment_id:
        failures.append("experiment lineage row missing expected experiment_id")
    if str((experiment_row or {}).get("dataset_version")) != "dataset.audit.v1":
        failures.append("experiment lineage row missing expected dataset_version")
    if str((experiment_row or {}).get("feature_version")) != "features.audit.v1":
        failures.append("experiment lineage row missing expected feature_version")
    if str((experiment_row or {}).get("alpha_id")) != alpha_id:
        failures.append("experiment lineage row missing expected alpha_id")
    if bool((experiment_row or {}).get("immutable_record")) is not True:
        failures.append("expected experiment record to remain immutable")

    if str((model_row or {}).get("model_id")) != model_id:
        failures.append("model provenance row missing expected model_id")
    if str((model_row or {}).get("experiment_id")) != experiment_id:
        failures.append("model provenance row missing expected experiment_id")
    if str((model_row or {}).get("dataset_version")) != "dataset.audit.v1":
        failures.append("model provenance row missing expected dataset_version")
    if str((model_row or {}).get("feature_version")) != "features.audit.v1":
        failures.append("model provenance row missing expected feature_version")
    if str((model_row or {}).get("state")) != "live":
        failures.append("expected latest model state to remain live in provenance scenario")

    if str((latest_model_transition or {}).get("to_state")) != "live":
        failures.append("expected latest model transition to end in live state")
    if str((latest_model_transition or {}).get("reason")) not in {"initial_registration", "self_improving_keep"}:
        failures.append("expected latest model transition reason to remain attributable")
    if str((latest_alpha_library or {}).get("state")) != "promoted":
        failures.append("expected alpha library state promoted after self-improving keep")
    if str((latest_alpha_event or {}).get("to_state")) != "promoted":
        failures.append("expected latest alpha status event to_state promoted")
    if str((latest_alpha_event or {}).get("reason")) != "self_improving_keep":
        failures.append("expected latest alpha status event reason self_improving_keep")
    if str((latest_promotion or {}).get("decision")) != "promote":
        failures.append("expected alpha promotion decision promote")
    if str((latest_promotion or {}).get("source_run_id")) != "self_improving_keep":
        failures.append("expected alpha promotion source_run_id self_improving_keep")

    if str((promoted_btc_signal or {}).get("dominant_alpha")) != alpha_id:
        failures.append("expected promoted runtime BTC signal to use promoted alpha")
    if float((promoted_btc_signal or {}).get("score", 0.0) or 0.0) <= 0.0:
        failures.append("expected promoted runtime BTC signal score to be positive")

    if str((promoted_run_record or {}).get("run_id")) != promoted_run:
        failures.append("runtime run row missing promoted run id")
    if str((promoted_run_record or {}).get("status")) != "success":
        failures.append("runtime run row missing success status")
    if str((promoted_run_record or {}).get("triggered_by")) != "verify_audit_provenance":
        failures.append("runtime run row missing triggered_by provenance")
    if str((promoted_step or {}).get("step_name")) != "orchestrator_cycle":
        failures.append("runtime step lineage missing orchestrator_cycle step")
    if str((promoted_step or {}).get("status")) != "success":
        failures.append("runtime step lineage missing successful step status")

    checkpoint_payload = {}
    if promoted_checkpoint and promoted_checkpoint.get("payload_json"):
        try:
            checkpoint_payload = json.loads(str(promoted_checkpoint["payload_json"]))
        except Exception:
            checkpoint_payload = {}
    if str((promoted_checkpoint or {}).get("checkpoint_name")) != "latest_orchestrator_run":
        failures.append("expected latest runtime checkpoint latest_orchestrator_run")
    if str(checkpoint_payload.get("run_id")) != promoted_run:
        failures.append("expected checkpoint payload run_id to match promoted runtime run")

    promoted_audit_event_types = [str(row.get("event_type")) for row in promoted_audit_logs]
    if promoted_audit_event_types != ["run_started", "checkpoint_created", "run_finished"]:
        failures.append("expected promoted runtime audit chain run_started -> checkpoint_created -> run_finished")
    if any(str(row.get("actor")) != "verify_audit_provenance" for row in promoted_audit_logs):
        failures.append("expected promoted runtime audit actors to stay attributable")

    guard_event_types = [str(row.get("event_type")) for row in guard_audit_logs]
    for required in ["resume", "kill_switch", "resume"]:
        if required not in guard_event_types:
            failures.append(f"expected guard audit logs to include {required}")
            break
    matching_guard_rows = [row for row in guard_audit_logs if str(row.get("actor")) == "verify_audit_provenance"]
    if len(matching_guard_rows) < 3:
        failures.append("expected attributable guard audit rows for baseline resume, halt, and resume")

    return {
        "status": "ok" if not failures else "failed",
        "lane": "audit_provenance",
        "registrations": registrations,
        "scenario": scenario,
        "artifacts": {
            "dataset_row": dataset_row,
            "feature_row": feature_row,
            "experiment_row": experiment_row,
            "model_row": model_row,
            "latest_model_transition": latest_model_transition,
            "latest_alpha_event": latest_alpha_event,
            "latest_alpha_library": latest_alpha_library,
            "latest_promotion": latest_promotion,
            "promoted_btc_signal": promoted_btc_signal,
            "promoted_run_record": promoted_run_record,
            "promoted_step": promoted_step,
            "promoted_checkpoint": promoted_checkpoint,
            "checkpoint_payload": checkpoint_payload,
            "promoted_audit_logs": promoted_audit_logs,
            "guard_audit_logs": guard_audit_logs,
        },
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify audit and provenance continuity across research, runtime, governance, and guard surfaces.")
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
        print(
            "lineage "
            f"experiment={result['artifacts']['experiment_row'].get('experiment_id')} "
            f"model={result['artifacts']['model_row'].get('model_id')} "
            f"alpha={result['artifacts']['promoted_btc_signal'].get('dominant_alpha')}"
        )
        print(
            "audit "
            f"run_events={len(result['artifacts']['promoted_audit_logs'])} "
            f"guard_events={len(result['artifacts']['guard_audit_logs'])}"
        )
        if result["failures"]:
            print("failures:")
            for failure in result["failures"]:
                print(f"- {failure}")

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
