from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Governance_runtime_control_packet02_slippage_guard_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-grtc-c2-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def _reset_runtime_state(container, execution_routes) -> None:
    execution_routes._execution_quality_summary_cache["expires_at"] = None
    execution_routes._execution_quality_summary_cache["payload"] = None
    for table in [
        "execution_quality_snapshots",
        "runtime_control_state",
        "execution_state_snapshots",
        "execution_block_reasons",
        "audit_logs",
    ]:
        try:
            container.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def _seed_quality(container, *, created_at: str, run_id: str, cycle_id: str, avg_slippage_bps: float) -> None:
    container.runtime_store.append(
        "execution_quality_snapshots",
        {
            "snapshot_id": f"snap-{run_id}",
            "created_at": created_at,
            "run_id": run_id,
            "cycle_id": cycle_id,
            "mode": "shadow",
            "order_count": 2,
            "fill_count": 2,
            "fill_rate": 1.0,
            "avg_slippage_bps": avg_slippage_bps,
            "latency_ms_p50": 20.0,
            "latency_ms_p95": 35.0,
        },
    )


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_packet02_plan_doc")
    else:
        plan_text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/governance/runtime-control/slippage-guard/latest",
            "/governance/runtime-control/slippage-guard/apply",
            "pause",
            "halt",
            "runtime control state",
        ]:
            if needle not in plan_text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.app.container import CONTAINER
    from ai_hedge_bot.api.routes import execution as execution_routes
    from ai_hedge_bot.services.governance_runtime_control_service import GovernanceRuntimeControlService

    _reset_runtime_state(CONTAINER, execution_routes)
    service = GovernanceRuntimeControlService()
    now = datetime.now(timezone.utc)

    _seed_quality(
        CONTAINER,
        created_at=(now + timedelta(seconds=2)).isoformat(),
        run_id="run-grtc-c2-pause",
        cycle_id="cycle-grtc-c2-pause",
        avg_slippage_bps=3.4,
    )
    latest = service.slippage_guard_latest()
    if latest.get("decision") != "pause":
        failures.append("pause_decision_expected")
    if latest.get("target_trading_state") != "paused":
        failures.append("pause_target_state_expected")
    if latest.get("current_trading_state") != "running":
        failures.append("initial_state_should_be_running")

    applied_pause = service.apply_slippage_guard_latest()
    pause_state = (applied_pause.get("applied_state") or {}).get("trading_state")
    if pause_state != "paused":
        failures.append("pause_apply_failed")

    _seed_quality(
        CONTAINER,
        created_at=(now + timedelta(seconds=5)).isoformat(),
        run_id="run-grtc-c2-halt",
        cycle_id="cycle-grtc-c2-halt",
        avg_slippage_bps=5.7,
    )
    latest_halt = service.slippage_guard_latest()
    if latest_halt.get("decision") != "halt":
        failures.append("halt_decision_expected")
    if latest_halt.get("target_trading_state") != "halted":
        failures.append("halt_target_state_expected")

    applied_halt = service.apply_slippage_guard_latest()
    halt_state = (applied_halt.get("applied_state") or {}).get("trading_state")
    if halt_state != "halted":
        failures.append("halt_apply_failed")

    current_state = service.runtime_service.get_trading_state()
    if current_state.get("trading_state") != "halted":
        failures.append("runtime_state_should_end_halted")

    audit_row = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT event_type, actor
        FROM audit_logs
        ORDER BY created_at DESC
        LIMIT 1
        """
    ) or {}
    if str(audit_row.get("event_type") or "") != "kill_switch":
        failures.append("halt_audit_event_missing")
    if str(audit_row.get("actor") or "") != "governance_runtime_control":
        failures.append("halt_audit_actor_mismatch")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
