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
from ai_hedge_bot.services.self_improving_service import SelfImprovingService  # noqa: E402
from ai_hedge_bot.services.runtime.runtime_service import RuntimeService  # noqa: E402
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
        fixed = datetime(2026, 4, 1, 16, 20, tzinfo=timezone.utc)
        if tz is None:
            return fixed.replace(tzinfo=None)
        return fixed.astimezone(tz)


def _reset_state() -> None:
    for table in RESET_TABLES:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def _register_lineage(alpha_id: str, experiment_id: str, model_id: str) -> None:
    calls = [
        ("/research-factory/datasets/register", {
            "dataset_id": "ds_multi_cycle",
            "dataset_version": "dataset.multi_cycle.v1",
            "source": "verify_multi_cycle_acceptance",
            "created_by": "verify_multi_cycle_acceptance",
        }),
        ("/research-factory/features/register", {
            "feature_id": "feat_multi_cycle",
            "feature_version": "features.multi_cycle.v1",
            "feature_list": ["momentum_8", "oi_delta"],
            "created_by": "verify_multi_cycle_acceptance",
        }),
        ("/alpha/generate", {
            "alpha_id": alpha_id,
            "alpha_family": "derivatives",
            "factor_type": "carry",
            "feature_dependencies": ["funding_rate", "oi_delta"],
        }),
        ("/research-factory/experiments/register", {
            "experiment_id": experiment_id,
            "dataset_version": "dataset.multi_cycle.v1",
            "feature_version": "features.multi_cycle.v1",
            "model_version": "model.multi_cycle.v1",
            "alpha_id": alpha_id,
            "strategy_id": "trend_core",
        }),
        ("/research-factory/validations/register", {
            "validation_id": "val_multi_cycle",
            "experiment_id": experiment_id,
            "summary_score": 0.84,
            "passed": True,
        }),
        ("/research-factory/models/register", {
            "model_id": model_id,
            "experiment_id": experiment_id,
            "dataset_version": "dataset.multi_cycle.v1",
            "feature_version": "features.multi_cycle.v1",
            "model_version": "model.multi_cycle.v1",
            "validation_metrics": {"summary_score": 0.84, "max_drawdown": 0.06},
            "state": "live",
        }),
    ]
    for path, payload in calls:
        response = client.post(path, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"{path} failed: {response.status_code} {response.text}")


def _decode(raw: str | None) -> dict[str, Any]:
    try:
        return json.loads(str(raw or "{}"))
    except Exception:
        return {}


def _bridge(run_id: str) -> dict[str, Any]:
    response = client.get(f"/execution/bridge/by-run/{run_id}")
    if response.status_code != 200:
        raise RuntimeError(f"/execution/bridge/by-run/{run_id} failed: {response.status_code}")
    return response.json()


def _cycle_artifacts(run_id: str, timestamp: str) -> dict[str, Any]:
    signal_row = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT symbol, dominant_alpha, metadata_json
        FROM signals
        WHERE created_at = ? AND symbol = 'BTCUSDT'
        LIMIT 1
        """,
        [timestamp],
    )
    checkpoint_row = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT payload_json
        FROM runtime_checkpoints
        WHERE run_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [run_id],
    )
    checkpoint_payload = _decode((checkpoint_row or {}).get("payload_json"))
    truth_state = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT state_key, state_value
        FROM truth_engine_state
        ORDER BY state_key ASC
        """
    )
    equity_count = CONTAINER.runtime_store.fetchone_dict("SELECT COUNT(*) AS c FROM equity_snapshots")
    return {
        "signal_row": signal_row,
        "signal_metadata": _decode((signal_row or {}).get("metadata_json")),
        "checkpoint_linkage": ((checkpoint_payload.get("details") or {}).get("runtime_governance_linkage") or {}),
        "bridge": _bridge(run_id),
        "truth_state": truth_state,
        "equity_snapshot_count": int((equity_count or {}).get("c", 0) or 0),
    }


def verify() -> dict[str, Any]:
    failures: list[str] = []
    alpha_id = "alpha.multi.cycle.acceptance"
    experiment_id = "exp_multi_cycle_acceptance"
    model_id = "model_multi_cycle_acceptance"

    _reset_state()
    _register_lineage(alpha_id, experiment_id, model_id)

    runtime_service = RuntimeService()
    runtime_service.resume_trading("multi-cycle acceptance baseline", actor="verify_multi_cycle_acceptance")
    original_datetime = signal_service_module.datetime
    signal_service_module.datetime = _FixedDateTime
    try:
        baseline = runtime_service.run_once(mode="paper", job_name="multi_cycle_acceptance_baseline", triggered_by="verify_multi_cycle_acceptance")
        self_improving = SelfImprovingService().evaluate_result_evidence(
            {
                "created_at": "2026-04-01T16:25:00+00:00",
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
                "notes": "verify_multi_cycle_acceptance keep",
            }
        )
        promoted_first = runtime_service.run_once(mode="paper", job_name="multi_cycle_acceptance_promoted_1", triggered_by="verify_multi_cycle_acceptance")
        promoted_second = runtime_service.run_once(mode="paper", job_name="multi_cycle_acceptance_promoted_2", triggered_by="verify_multi_cycle_acceptance")
    finally:
        signal_service_module.datetime = original_datetime

    baseline_artifacts = _cycle_artifacts(baseline["run_id"], baseline["result"]["timestamp"])
    first_artifacts = _cycle_artifacts(promoted_first["run_id"], promoted_first["result"]["timestamp"])
    second_artifacts = _cycle_artifacts(promoted_second["run_id"], promoted_second["result"]["timestamp"])

    if baseline["status"] != "ok":
        failures.append("baseline cycle did not complete successfully")
    if promoted_first["status"] != "ok":
        failures.append("first promoted cycle did not complete successfully")
    if promoted_second["status"] != "ok":
        failures.append("second promoted cycle did not complete successfully")
    if self_improving.get("decision") != "keep":
        failures.append("expected self-improving decision keep for multi-cycle scenario")

    if str((baseline_artifacts["signal_row"] or {}).get("dominant_alpha")) != "phase6_dynamic_alpha":
        failures.append("expected baseline BTC dominant_alpha to remain phase6_dynamic_alpha")

    for label, artifacts in [("first", first_artifacts), ("second", second_artifacts)]:
        signal_row = artifacts["signal_row"] or {}
        metadata = artifacts["signal_metadata"] or {}
        linkage = artifacts["checkpoint_linkage"] or {}
        bridge = artifacts["bridge"] or {}
        truth_keys = {str(row.get("state_key")) for row in artifacts["truth_state"]}

        if str(signal_row.get("dominant_alpha")) != alpha_id:
            failures.append(f"expected {label} promoted cycle dominant_alpha to remain promoted alpha")
        if bool(metadata.get("runtime_alpha_linked")) is not True:
            failures.append(f"expected {label} promoted cycle signal metadata runtime_alpha_linked=true")
        if str(metadata.get("runtime_model_id")) != model_id:
            failures.append(f"expected {label} promoted cycle runtime_model_id to match model_id")
        if str(metadata.get("runtime_decision_source")) != "self_improving_keep":
            failures.append(f"expected {label} promoted cycle decision_source=self_improving_keep")
        if str(linkage.get("alpha_id")) != alpha_id:
            failures.append(f"expected {label} promoted cycle checkpoint linkage alpha_id to match")
        if str(linkage.get("model_id")) != model_id:
            failures.append(f"expected {label} promoted cycle checkpoint linkage model_id to match")
        if str(linkage.get("decision_source")) != "self_improving_keep":
            failures.append(f"expected {label} promoted cycle checkpoint linkage decision_source=self_improving_keep")
        if bridge.get("event_chain_complete") is not True:
            failures.append(f"expected {label} promoted cycle execution bridge complete")
        if label == "first" and str(bridge.get("bridge_state")) != "filled":
            failures.append("expected first promoted cycle execution bridge filled")
        if label == "second" and str(bridge.get("bridge_state")) not in {"filled", "no_decision"}:
            failures.append("expected second promoted cycle execution bridge to remain explicit via filled or no_decision")
        if not {"positions_last_fill", "equity_last_fill", "equity_snapshot_state"}.issubset(truth_keys):
            failures.append(f"expected {label} promoted cycle truth state keys to remain present")

    if second_artifacts["equity_snapshot_count"] < first_artifacts["equity_snapshot_count"]:
        failures.append("expected equity snapshot count not to regress in second promoted cycle")

    return {
        "status": "ok" if not failures else "failed",
        "lane": "multi_cycle_acceptance",
        "baseline_run_id": baseline["run_id"],
        "first_promoted_run_id": promoted_first["run_id"],
        "second_promoted_run_id": promoted_second["run_id"],
        "first_promoted_artifacts": first_artifacts,
        "second_promoted_artifacts": second_artifacts,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify multi-cycle acceptance across consecutive promoted runtime cycles.")
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
            "runs "
            f"baseline={result['baseline_run_id']} "
            f"first={result['first_promoted_run_id']} "
            f"second={result['second_promoted_run_id']}"
        )
        if result["failures"]:
            print("failures:")
            for failure in result["failures"]:
                print(f"- {failure}")

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
