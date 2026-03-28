from __future__ import annotations

from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app
from ai_hedge_bot.api.routes import execution as execution_routes
from ai_hedge_bot.api.routes import runtime as runtime_routes
from ai_hedge_bot.services.runtime.runtime_service import RuntimeService


client = TestClient(app)


def _reset_phase5_close4_state() -> None:
    tables = [
        "runtime_control_state",
        "runtime_runs",
        "runtime_run_steps",
        "runtime_checkpoints",
        "runtime_events",
        "audit_logs",
        "execution_plans",
        "execution_orders",
        "execution_fills",
        "execution_quality_snapshots",
        "execution_state_snapshots",
        "execution_block_reasons",
        "signals",
        "alpha_signal_snapshots",
        "portfolio_signal_decisions",
        "portfolio_positions",
        "portfolio_snapshots",
        "rebalance_plans",
        "orchestrator_runs",
        "orchestrator_cycles",
        "scheduler_runs",
        "scheduler_jobs",
    ]
    for table in tables:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass
    execution_routes._execution_view_cache["expires_at"] = None
    execution_routes._execution_view_cache["key"] = None
    execution_routes._execution_view_cache["payload"] = None
    execution_routes._execution_bridge_cache["expires_at"] = None
    execution_routes._execution_bridge_cache["payload"] = None
    runtime_routes._runtime_status_cache = None
    runtime_routes._runtime_runs_cache.clear()


def _normalize_halted_policy_outcome() -> dict:
    state = client.get("/runtime/trading-state").json()
    execution_state = client.get("/execution/state/latest").json()
    reasons = client.get("/execution/block-reasons/latest").json()["items"]
    jobs = client.get("/scheduler/jobs").json()["items"]
    execution_jobs = [
        item for item in jobs
        if any(token in " ".join([
            str(item.get("job_id", "") or ""),
            str(item.get("job_name", "") or ""),
            str(item.get("mode", "") or ""),
        ]).lower() for token in ("cycle", "runtime", "orchestrator", "paper", "shadow", "rebalance"))
    ]
    return {
        "trading_state": str(state.get("trading_state", "")).lower(),
        "execution_state": str(execution_state.get("execution_state", "")).lower(),
        "reason_codes": sorted({str(item.get("code") or "") for item in reasons}),
        "execution_jobs_blocked": all(bool(item.get("execution_blocked")) for item in execution_jobs),
        "execution_jobs_state": sorted({str(item.get("trading_state", "")).lower() for item in execution_jobs}),
    }


def _normalize_resume_policy_outcome(run_response: dict) -> dict:
    execution_state = client.get("/execution/state/latest").json()
    trading_state = client.get("/runtime/trading-state").json()
    return {
        "run_status": str(run_response.get("status", "")).lower(),
        "result_status": str((run_response.get("result") or {}).get("status", "")).lower(),
        "trading_state": str(trading_state.get("trading_state", "")).lower(),
        "execution_state": str(execution_state.get("execution_state", "")).lower(),
        "has_execution_artifacts": all(
            int(
                (CONTAINER.runtime_store.fetchone_dict(f"SELECT COUNT(*) AS c FROM {table}") or {"c": 0}).get("c") or 0
            ) > 0
            for table in ("rebalance_plans", "execution_plans", "execution_orders", "execution_fills")
        ),
    }


def test_phase5_close4_policy_decision_is_consistent_across_equivalent_entrypoints() -> None:
    service = RuntimeService()

    _reset_phase5_close4_state()
    client.post("/runtime/resume")
    api_halt = client.post("/runtime/kill-switch")
    assert api_halt.status_code == 200
    api_halt_outcome = _normalize_halted_policy_outcome()
    blocked_api = client.post("/runtime/run-once?mode=paper").json()
    assert blocked_api["status"] == "blocked"
    assert blocked_api["reason_code"] == "execution_disabled"

    _reset_phase5_close4_state()
    service.resume_trading("reset via service", actor="test")
    service_halt = service.halt_trading("Kill switch triggered in V12 runtime", actor="test")
    assert service_halt["trading_state"] == "halted"
    service_halt_outcome = _normalize_halted_policy_outcome()
    blocked_service = service.run_once(mode="paper", job_name="runtime_run_once", triggered_by="api")
    assert blocked_service["status"] == "blocked"
    assert blocked_service["reason_code"] == "execution_disabled"

    assert api_halt_outcome == service_halt_outcome
    assert api_halt_outcome["trading_state"] == "halted"
    assert api_halt_outcome["execution_state"] in {"halted", "blocked"}
    assert "risk_halted" in api_halt_outcome["reason_codes"]
    assert api_halt_outcome["execution_jobs_blocked"] is True

    _reset_phase5_close4_state()
    service.halt_trading("Kill switch triggered in V12 runtime", actor="test")
    client.post("/runtime/resume")
    resumed_via_api = client.post("/runtime/run-once?mode=paper").json()
    api_resume_outcome = _normalize_resume_policy_outcome(resumed_via_api)

    _reset_phase5_close4_state()
    service.halt_trading("Kill switch triggered in V12 runtime", actor="test")
    service.resume_trading("Runtime resumed", actor="test")
    resumed_via_service = service.run_once(mode="paper", job_name="runtime_run_once", triggered_by="api")
    service_resume_outcome = _normalize_resume_policy_outcome(resumed_via_service)

    assert api_resume_outcome == service_resume_outcome
    assert api_resume_outcome["run_status"] == "ok"
    assert api_resume_outcome["result_status"] == "ok"
    assert api_resume_outcome["trading_state"] == "running"
    assert api_resume_outcome["execution_state"] not in {"halted", "blocked"}
    assert api_resume_outcome["has_execution_artifacts"] is True
