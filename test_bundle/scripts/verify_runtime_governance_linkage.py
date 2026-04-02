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
        fixed = datetime(2026, 4, 1, 15, 15, tzinfo=timezone.utc)
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
        (
            "/research-factory/datasets/register",
            {
                "dataset_id": "ds_runtime_linkage",
                "dataset_version": "dataset.runtime_linkage.v1",
                "source": "verify_runtime_governance_linkage",
                "created_by": "verify_runtime_governance_linkage",
            },
        ),
        (
            "/research-factory/features/register",
            {
                "feature_id": "feat_runtime_linkage",
                "feature_version": "features.runtime_linkage.v1",
                "feature_list": ["momentum_8", "oi_delta"],
                "created_by": "verify_runtime_governance_linkage",
            },
        ),
        (
            "/alpha/generate",
            {
                "alpha_id": alpha_id,
                "alpha_family": "derivatives",
                "factor_type": "carry",
                "feature_dependencies": ["funding_rate", "oi_delta"],
            },
        ),
        (
            "/research-factory/experiments/register",
            {
                "experiment_id": experiment_id,
                "dataset_version": "dataset.runtime_linkage.v1",
                "feature_version": "features.runtime_linkage.v1",
                "model_version": "model.runtime_linkage.v1",
                "alpha_id": alpha_id,
                "strategy_id": "trend_core",
            },
        ),
        (
            "/research-factory/validations/register",
            {
                "validation_id": "val_runtime_linkage",
                "experiment_id": experiment_id,
                "summary_score": 0.84,
                "passed": True,
            },
        ),
        (
            "/research-factory/models/register",
            {
                "model_id": model_id,
                "experiment_id": experiment_id,
                "dataset_version": "dataset.runtime_linkage.v1",
                "feature_version": "features.runtime_linkage.v1",
                "model_version": "model.runtime_linkage.v1",
                "validation_metrics": {"summary_score": 0.84, "max_drawdown": 0.06},
                "state": "live",
            },
        ),
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


def verify() -> dict[str, Any]:
    failures: list[str] = []
    alpha_id = "alpha.runtime.linkage"
    experiment_id = "exp_runtime_linkage"
    model_id = "model_runtime_linkage"

    _reset_state()
    _register_lineage(alpha_id, experiment_id, model_id)

    runtime_service = RuntimeService()
    runtime_service.resume_trading("runtime governance linkage baseline", actor="verify_runtime_governance_linkage")
    original_datetime = signal_service_module.datetime
    signal_service_module.datetime = _FixedDateTime
    try:
        baseline = runtime_service.run_once(mode="paper", job_name="runtime_governance_linkage_baseline", triggered_by="verify_runtime_governance_linkage")
        self_improving = SelfImprovingService().evaluate_result_evidence(
            {
                "created_at": "2026-04-01T15:20:00+00:00",
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
                "notes": "verify_runtime_governance_linkage keep",
            }
        )
        promoted = runtime_service.run_once(mode="paper", job_name="runtime_governance_linkage_promoted", triggered_by="verify_runtime_governance_linkage")
    finally:
        signal_service_module.datetime = original_datetime

    promoted_run_id = promoted["run_id"]
    promoted_ts = promoted["result"]["timestamp"]
    signal_row = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT symbol, dominant_alpha, metadata_json
        FROM signals
        WHERE created_at = ? AND symbol = 'BTCUSDT'
        LIMIT 1
        """,
        [promoted_ts],
    )
    signal_metadata = _decode((signal_row or {}).get("metadata_json"))
    snapshot_row = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT summary_json
        FROM alpha_signal_snapshots
        WHERE run_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [promoted_run_id],
    )
    snapshot_summary = _decode((snapshot_row or {}).get("summary_json"))
    checkpoint_row = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT payload_json
        FROM runtime_checkpoints
        WHERE run_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [promoted_run_id],
    )
    checkpoint_payload = _decode((checkpoint_row or {}).get("payload_json"))
    checkpoint_linkage = ((checkpoint_payload.get("details") or {}).get("runtime_governance_linkage") or {})
    snapshot_linkage = snapshot_summary.get("runtime_governance_linkage") or {}

    if baseline["status"] != "ok":
        failures.append("baseline runtime cycle did not complete successfully")
    if promoted["status"] != "ok":
        failures.append("promoted runtime cycle did not complete successfully")
    if self_improving.get("decision") != "keep":
        failures.append("expected self-improving decision keep for runtime governance linkage scenario")

    if str((signal_row or {}).get("dominant_alpha")) != alpha_id:
        failures.append("expected promoted BTC signal dominant_alpha to equal promoted alpha_id")
    if bool(signal_metadata.get("runtime_alpha_linked")) is not True:
        failures.append("expected promoted BTC signal metadata runtime_alpha_linked=true")
    if str(signal_metadata.get("runtime_alpha_id")) != alpha_id:
        failures.append("expected signal metadata runtime_alpha_id to match alpha_id")
    if str(signal_metadata.get("runtime_model_id")) != model_id:
        failures.append("expected signal metadata runtime_model_id to match model_id")
    if str(signal_metadata.get("runtime_decision_source")) != "self_improving_keep":
        failures.append("expected signal metadata runtime_decision_source=self_improving_keep")

    if str(snapshot_linkage.get("alpha_id")) != alpha_id:
        failures.append("expected alpha signal snapshot linkage alpha_id to match")
    if str(snapshot_linkage.get("model_id")) != model_id:
        failures.append("expected alpha signal snapshot linkage model_id to match")
    if str(snapshot_linkage.get("decision_source")) != "self_improving_keep":
        failures.append("expected alpha signal snapshot linkage decision_source=self_improving_keep")

    if str(checkpoint_linkage.get("alpha_id")) != alpha_id:
        failures.append("expected checkpoint linkage alpha_id to match")
    if str(checkpoint_linkage.get("model_id")) != model_id:
        failures.append("expected checkpoint linkage model_id to match")
    if str(checkpoint_linkage.get("decision_source")) != "self_improving_keep":
        failures.append("expected checkpoint linkage decision_source=self_improving_keep")
    if str(checkpoint_linkage.get("symbol")) != "BTCUSDT":
        failures.append("expected checkpoint linkage symbol BTCUSDT")

    return {
        "status": "ok" if not failures else "failed",
        "lane": "runtime_governance_linkage",
        "baseline_run_id": baseline["run_id"],
        "promoted_run_id": promoted_run_id,
        "signal_row": signal_row,
        "signal_metadata": signal_metadata,
        "snapshot_linkage": snapshot_linkage,
        "checkpoint_linkage": checkpoint_linkage,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify runtime cycles carry explicit governance linkage metadata.")
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
            "linkage "
            f"alpha_id={result['checkpoint_linkage'].get('alpha_id')} "
            f"model_id={result['checkpoint_linkage'].get('model_id')} "
            f"decision_source={result['checkpoint_linkage'].get('decision_source')}"
        )
        if result["failures"]:
            print("failures:")
            for failure in result["failures"]:
                print(f"- {failure}")

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
