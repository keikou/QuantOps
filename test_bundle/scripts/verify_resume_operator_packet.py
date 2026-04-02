from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
V12_APP = REPO_ROOT / "apps" / "v12-api"
if str(V12_APP) not in sys.path:
    sys.path.insert(0, str(V12_APP))

from fastapi.testclient import TestClient  # noqa: E402

from ai_hedge_bot.app.container import CONTAINER  # noqa: E402
from ai_hedge_bot.app.main import app  # noqa: E402
from ai_hedge_bot.core.enums import Mode  # noqa: E402
from ai_hedge_bot.services.live_trading_service import LiveTradingService  # noqa: E402
from ai_hedge_bot.services.runtime.runtime_service import RuntimeService  # noqa: E402
from ai_hedge_bot.services.self_improving_service import SelfImprovingService  # noqa: E402
from ai_hedge_bot.signal import signal_service as signal_service_module  # noqa: E402


client = TestClient(app)

RESET_TABLES = [
    "runtime_control_state","runtime_runs","runtime_run_steps","scheduler_runs","runtime_checkpoints","runtime_events",
    "audit_logs","signals","signal_evaluations","alpha_signal_snapshots","alpha_candidates","portfolio_signal_decisions",
    "portfolio_diagnostics","portfolio_snapshots","portfolio_positions","rebalance_plans","execution_plans","execution_orders",
    "execution_fills","execution_quality_snapshots","execution_state_snapshots","execution_block_reasons","shadow_orders",
    "shadow_fills","shadow_pnl_snapshots","orchestrator_runs","orchestrator_cycles","market_prices_latest","market_prices_history",
    "position_snapshots_latest","position_snapshots_history","position_snapshot_versions","equity_snapshots","cash_ledger",
    "truth_engine_state","dataset_registry","feature_registry","experiment_tracker","validation_registry","model_registry",
    "model_state_transitions","model_live_reviews","alpha_registry","alpha_status_events","alpha_library","alpha_promotions",
    "alpha_demotions","alpha_rankings","live_orders","live_fills","live_account_balances","live_reconciliation_events","live_incidents",
]


class _FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        fixed = datetime(2026, 4, 2, 2, 40, tzinfo=timezone.utc)
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


def _seed() -> None:
    alpha_id = "alpha.resume.packet"
    experiment_id = "exp_resume_packet"
    model_id = "model_resume_packet"
    calls = [
        ("/research-factory/datasets/register", {"dataset_id": "ds_resume_packet", "dataset_version": "dataset.resume_packet.v1", "source": "verify_resume_operator_packet", "created_by": "verify_resume_operator_packet"}),
        ("/research-factory/features/register", {"feature_id": "feat_resume_packet", "feature_version": "features.resume_packet.v1", "feature_list": ["momentum_8", "oi_delta"], "created_by": "verify_resume_operator_packet"}),
        ("/alpha/generate", {"alpha_id": alpha_id, "alpha_family": "derivatives", "factor_type": "carry", "feature_dependencies": ["funding_rate", "oi_delta"]}),
        ("/research-factory/experiments/register", {"experiment_id": experiment_id, "dataset_version": "dataset.resume_packet.v1", "feature_version": "features.resume_packet.v1", "model_version": "model.resume_packet.v1", "alpha_id": alpha_id, "strategy_id": "trend_core"}),
        ("/research-factory/validations/register", {"validation_id": "val_resume_packet", "experiment_id": experiment_id, "summary_score": 0.84, "passed": True}),
        ("/research-factory/models/register", {"model_id": model_id, "experiment_id": experiment_id, "dataset_version": "dataset.resume_packet.v1", "feature_version": "features.resume_packet.v1", "model_version": "model.resume_packet.v1", "validation_metrics": {"summary_score": 0.84, "max_drawdown": 0.06}, "state": "live"}),
        ("/research-factory/promotion/evaluate", {"alpha_id": alpha_id, "model_id": model_id, "strategy_id": "trend_core", "summary_score": 0.84, "decision": "promote", "decision_source": "verify_resume_operator_packet"}),
    ]
    for path, payload in calls:
        response = client.post(path, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"{path} failed: {response.status_code} {response.text}")

    runtime_service = RuntimeService()
    runtime_service.resume_trading("resume operator packet baseline", actor="verify_resume_operator_packet")
    original_datetime = signal_service_module.datetime
    signal_service_module.datetime = _FixedDateTime
    try:
        runtime_service.run_once(mode="paper", job_name="resume_packet_baseline", triggered_by="verify_resume_operator_packet")
        decision = SelfImprovingService().evaluate_result_evidence({
            "created_at": "2026-04-02T02:45:00+00:00","model_id": model_id,"strategy_id": "trend_core","expected_return": 0.12,
            "realized_return": 0.11,"hit_rate": 0.68,"turnover": 0.32,"drawdown": -0.05,"slippage_bps": 4.0,"fill_rate": 0.91,
            "risk_usage": 0.52,"notes": "verify_resume_operator_packet keep",
        })
        if decision.get("decision") != "keep":
            raise RuntimeError("expected self-improving keep decision")
        runtime_service.run_once(mode="paper", job_name="resume_packet_promoted_1", triggered_by="verify_resume_operator_packet")
        runtime_service.run_once(mode="paper", job_name="resume_packet_promoted_2", triggered_by="verify_resume_operator_packet")
    finally:
        signal_service_module.datetime = original_datetime

    live_service = LiveTradingService()
    live_service.runtime_service.resume_trading("resume operator packet recovery", actor="verify_resume_operator_packet")
    submitted = live_service.submit_live_order(symbol="BNBUSDT", side="buy", qty=2.0, urgency="high", target_weight=0.28, approved=True, mode=Mode.LIVE)
    if submitted["status"] != "ok":
        raise RuntimeError(f"submit_live_order failed: {submitted}")
    result = live_service.replay_live_fill(
        live_order_id=submitted["live_order_id"], venue_order_id=submitted["venue_order_id"], symbol="BNBUSDT", side="buy",
        fill_qty=1.0, fill_price=610.0, free_balance=6400.0, locked_balance=1500.0, matched=False,
    )
    if result["status"] != "incident":
        raise RuntimeError(f"unexpected reconciliation status: {result}")
    recovered = live_service.recover_live_incident(
        live_order_id=submitted["live_order_id"], venue_order_id=submitted["venue_order_id"],
        resolution_note="verify_resume_operator_packet", actor="verify_resume_operator_packet",
    )
    if recovered["status"] != "ok":
        raise RuntimeError(f"recover_live_incident failed: {recovered}")
    client.post("/system/hardening-evidence-snapshot/save")
    client.post("/system/hardening-architect-handoff/save")


def verify() -> dict[str, object]:
    failures: list[str] = []
    _reset_state()
    _seed()

    save_response = client.post("/system/resume-operator-packet/save")
    if save_response.status_code != 200:
        raise RuntimeError(f"/system/resume-operator-packet/save failed: {save_response.status_code} {save_response.text}")
    saved = save_response.json()
    latest_response = client.get("/system/resume-operator-packet/latest")
    if latest_response.status_code != 200:
        raise RuntimeError(f"/system/resume-operator-packet/latest failed: {latest_response.status_code} {latest_response.text}")
    latest = latest_response.json()

    content = str(saved.get("content") or "")
    if saved.get("status") != "ok":
        failures.append("save response did not return status ok")
    if latest.get("status") != "ok":
        failures.append("latest response did not return status ok")
    if not str(saved.get("path") or ""):
        failures.append("resume operator packet missing path")
    for token in [
        "Resume Operator Packet Latest",
        "System Reliability Hardening Track",
        "codex/post-phase7-hardening",
        "Core Entry Points",
        "Recommended Verifiers",
        "Readiness",
        "Overall Ready: `True`",
    ]:
        if token not in content:
            failures.append(f"resume operator packet missing token: {token}")
    if content != str(latest.get("content") or ""):
        failures.append("latest packet content differs from saved content")

    return {
        "status": "ok" if not failures else "failed",
        "lane": "resume_operator_packet",
        "path": saved.get("path"),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the resume operator packet can be generated from live manifest data.")
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
        print(f"path={result.get('path')}")
        if result["failures"]:
            print("failures:")
            for failure in result["failures"]:
                print(f"- {failure}")

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
