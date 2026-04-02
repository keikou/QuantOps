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
from ai_hedge_bot.app.main import app  # noqa: E402
from ai_hedge_bot.services.runtime.runtime_service import RuntimeService  # noqa: E402
from ai_hedge_bot.services.self_improving_service import SelfImprovingService  # noqa: E402
from ai_hedge_bot.signal import signal_service as signal_service_module  # noqa: E402


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
]


class _FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        fixed = datetime(2026, 4, 1, 17, 10, tzinfo=timezone.utc)
        if tz is None:
            return fixed.replace(tzinfo=None)
        return fixed.astimezone(tz)


def _reset_state() -> None:
    CONTAINER.latest_portfolio_diagnostics = {}
    CONTAINER.latest_orchestrator_run = {}
    CONTAINER.latest_execution_quality = {}
    for table in RESET_TABLES:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def _register_lineage(alpha_id: str, experiment_id: str, model_id: str) -> None:
    calls = [
        ("/research-factory/datasets/register", {
            "dataset_id": "ds_operator_bundle",
            "dataset_version": "dataset.operator_bundle.v1",
            "source": "verify_operator_diagnostic_bundle",
            "created_by": "verify_operator_diagnostic_bundle",
        }),
        ("/research-factory/features/register", {
            "feature_id": "feat_operator_bundle",
            "feature_version": "features.operator_bundle.v1",
            "feature_list": ["momentum_8", "oi_delta"],
            "created_by": "verify_operator_diagnostic_bundle",
        }),
        ("/alpha/generate", {
            "alpha_id": alpha_id,
            "alpha_family": "derivatives",
            "factor_type": "carry",
            "feature_dependencies": ["funding_rate", "oi_delta"],
        }),
        ("/research-factory/experiments/register", {
            "experiment_id": experiment_id,
            "dataset_version": "dataset.operator_bundle.v1",
            "feature_version": "features.operator_bundle.v1",
            "model_version": "model.operator_bundle.v1",
            "alpha_id": alpha_id,
            "strategy_id": "trend_core",
        }),
        ("/research-factory/validations/register", {
            "validation_id": "val_operator_bundle",
            "experiment_id": experiment_id,
            "summary_score": 0.84,
            "passed": True,
        }),
        ("/research-factory/models/register", {
            "model_id": model_id,
            "experiment_id": experiment_id,
            "dataset_version": "dataset.operator_bundle.v1",
            "feature_version": "features.operator_bundle.v1",
            "model_version": "model.operator_bundle.v1",
            "validation_metrics": {"summary_score": 0.84, "max_drawdown": 0.06},
            "state": "live",
        }),
    ]
    for path, payload in calls:
        response = client.post(path, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"{path} failed: {response.status_code} {response.text}")


def verify() -> dict[str, Any]:
    failures: list[str] = []
    alpha_id = "alpha.operator.bundle"
    experiment_id = "exp_operator_bundle"
    model_id = "model_operator_bundle"

    _reset_state()
    _register_lineage(alpha_id, experiment_id, model_id)

    runtime_service = RuntimeService()
    runtime_service.resume_trading("operator diagnostic bundle baseline", actor="verify_operator_diagnostic_bundle")
    original_datetime = signal_service_module.datetime
    signal_service_module.datetime = _FixedDateTime
    try:
        baseline = runtime_service.run_once(mode="paper", job_name="operator_bundle_baseline", triggered_by="verify_operator_diagnostic_bundle")
        decision = SelfImprovingService().evaluate_result_evidence(
            {
                "created_at": "2026-04-01T17:15:00+00:00",
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
                "notes": "verify_operator_diagnostic_bundle keep",
            }
        )
        promoted = runtime_service.run_once(mode="paper", job_name="operator_bundle_promoted", triggered_by="verify_operator_diagnostic_bundle")
    finally:
        signal_service_module.datetime = original_datetime

    response = client.get("/system/operator-diagnostic-bundle")
    if response.status_code != 200:
        raise RuntimeError(f"/system/operator-diagnostic-bundle failed: {response.status_code} {response.text}")
    bundle = response.json()

    run_id = promoted["run_id"]
    cycle_id = promoted["result"]["cycle_id"]
    linkage = bundle.get("runtime_governance_linkage") or {}
    consistency = bundle.get("consistency") or {}
    operator_summary = bundle.get("operator_summary") or {}
    execution_bridge = bundle.get("execution_bridge") or {}
    execution_quality = bundle.get("execution_quality") or {}
    portfolio_overview = bundle.get("portfolio_overview") or {}
    signal_snapshot = bundle.get("signal_snapshot") or {}
    orchestrator_run = bundle.get("latest_orchestrator_run") or {}
    config_provenance = bundle.get("config_provenance") or {}
    deploy_provenance = bundle.get("deploy_provenance") or {}

    if baseline["status"] != "ok":
        failures.append("baseline cycle did not complete successfully")
    if promoted["status"] != "ok":
        failures.append("promoted cycle did not complete successfully")
    if decision.get("decision") != "keep":
        failures.append("expected self-improving decision keep for operator diagnostic bundle scenario")

    if str(bundle.get("run_id")) != run_id:
        failures.append("bundle run_id does not match promoted run_id")
    if str(bundle.get("cycle_id")) != cycle_id:
        failures.append("bundle cycle_id does not match promoted cycle_id")
    if str((bundle.get("runtime_run") or {}).get("run_id")) != run_id:
        failures.append("runtime_run run_id does not match promoted run_id")
    if str(execution_bridge.get("run_id")) != run_id:
        failures.append("execution_bridge run_id does not match promoted run_id")
    if str(execution_bridge.get("cycle_id")) != cycle_id:
        failures.append("execution_bridge cycle_id does not match promoted cycle_id")
    if str(execution_quality.get("run_id")) != run_id:
        failures.append("execution_quality run_id does not match promoted run_id")
    if str((portfolio_overview.get("snapshot") or {}).get("run_id")) != run_id:
        failures.append("portfolio_overview snapshot run_id does not match promoted run_id")
    if str((signal_snapshot.get("snapshot") or {}).get("run_id")) != run_id:
        failures.append("signal_snapshot run_id does not match promoted run_id")
    if str(orchestrator_run.get("run_id")) != run_id:
        failures.append("latest_orchestrator_run run_id does not match promoted run_id")
    if str(orchestrator_run.get("cycle_id")) != cycle_id:
        failures.append("latest_orchestrator_run cycle_id does not match promoted cycle_id")

    if str(linkage.get("alpha_id")) != alpha_id:
        failures.append("bundle runtime_governance_linkage alpha_id does not match promoted alpha")
    if str(linkage.get("model_id")) != model_id:
        failures.append("bundle runtime_governance_linkage model_id does not match promoted model")
    if str(linkage.get("decision_source")) != "self_improving_keep":
        failures.append("bundle runtime_governance_linkage decision_source does not match expected keep source")

    if not str(config_provenance.get("fingerprint") or ""):
        failures.append("bundle missing config_provenance fingerprint")
    if not str(deploy_provenance.get("fingerprint") or ""):
        failures.append("bundle missing deploy_provenance fingerprint")
    if operator_summary.get("event_chain_complete") is not True:
        failures.append("bundle operator_summary event_chain_complete should be true")
    if str(operator_summary.get("bridge_state")) != "filled":
        failures.append("bundle operator_summary bridge_state should be filled for promoted cycle")
    if consistency.get("operator_ready") is not True:
        failures.append("bundle consistency operator_ready should be true")
    if list(consistency.get("mismatches") or []):
        failures.append("bundle consistency mismatches should be empty")

    return {
        "status": "ok" if not failures else "failed",
        "lane": "operator_diagnostic_bundle",
        "baseline_run_id": baseline["run_id"],
        "promoted_run_id": run_id,
        "bundle": {
            "run_id": bundle.get("run_id"),
            "cycle_id": bundle.get("cycle_id"),
            "operator_summary": operator_summary,
            "runtime_governance_linkage": linkage,
            "config_fingerprint": config_provenance.get("fingerprint"),
            "deploy_fingerprint": deploy_provenance.get("fingerprint"),
            "consistency": consistency,
        },
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the operator diagnostic bundle exposes coherent cross-surface evidence for the latest runtime cycle.")
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
            "bundle "
            f"run_id={result['bundle'].get('run_id')} "
            f"bridge_state={(result['bundle'].get('operator_summary') or {}).get('bridge_state')} "
            f"operator_ready={(result['bundle'].get('consistency') or {}).get('operator_ready')}"
        )
        if result["failures"]:
            print("failures:")
            for failure in result["failures"]:
                print(f"- {failure}")

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
