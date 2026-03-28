from __future__ import annotations

from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app
from ai_hedge_bot.services.runtime.runtime_service import RuntimeService


client = TestClient(app)


def _reset_phase5_close2_state() -> None:
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


def _count(table: str) -> int:
    row = CONTAINER.runtime_store.fetchone_dict(f"SELECT COUNT(*) AS c FROM {table}") or {"c": 0}
    return int(row.get("c") or 0)


def test_phase5_close2_halt_propagates_to_all_runtime_entrypoints_without_bypass() -> None:
    _reset_phase5_close2_state()
    service = RuntimeService()

    client.post("/runtime/resume")
    kill = client.post("/runtime/kill-switch")
    assert kill.status_code == 200
    assert kill.json()["trading_state"] == "halted"

    counts_before = {
        "runtime_runs": _count("runtime_runs"),
        "scheduler_runs": _count("scheduler_runs"),
        "rebalance_plans": _count("rebalance_plans"),
        "execution_plans": _count("execution_plans"),
        "execution_orders": _count("execution_orders"),
        "execution_fills": _count("execution_fills"),
    }

    blocked_api = client.post("/runtime/run-once?mode=paper")
    assert blocked_api.status_code == 200
    blocked_api_body = blocked_api.json()
    assert blocked_api_body["status"] == "blocked"
    assert blocked_api_body["reason_code"] == "execution_disabled"
    assert blocked_api_body["trading_state"] == "halted"

    blocked_loop = service.run_once(mode="paper", job_name="paper_runtime_loop", triggered_by="startup_loop")
    assert blocked_loop["status"] == "blocked"
    assert blocked_loop["reason_code"] == "execution_disabled"
    assert blocked_loop["trading_state"] == "halted"

    blocked_next = service.run_once(mode="paper", job_name="paper_rebalance_loop", triggered_by="scheduler_loop")
    assert blocked_next["status"] == "blocked"
    assert blocked_next["reason_code"] == "execution_disabled"
    assert blocked_next["trading_state"] == "halted"

    counts_after = {
        "runtime_runs": _count("runtime_runs"),
        "scheduler_runs": _count("scheduler_runs"),
        "rebalance_plans": _count("rebalance_plans"),
        "execution_plans": _count("execution_plans"),
        "execution_orders": _count("execution_orders"),
        "execution_fills": _count("execution_fills"),
    }
    assert counts_after == counts_before

    for run_id in [blocked_api_body["run_id"], blocked_loop["run_id"], blocked_next["run_id"]]:
        reasons = client.get(f"/runtime/reasons/by-run/{run_id}")
        assert reasons.status_code == 200
        items = reasons.json()["items"]
        assert items
        assert items[0]["status"] == "blocked"
        assert items[0]["reason_code"] == "execution_disabled"

    latest_state = client.get("/execution/state/latest")
    assert latest_state.status_code == 200
    latest_state_body = latest_state.json()
    assert str(latest_state_body["trading_state"]).lower() == "halted"
    assert str(latest_state_body["execution_state"]).lower() in {"halted", "blocked"}
    assert latest_state_body["active_plan_count"] == 0
    assert latest_state_body["open_order_count"] == 0

    latest_reasons = client.get("/execution/block-reasons/latest")
    assert latest_reasons.status_code == 200
    reason_codes = {str(item["code"]) for item in latest_reasons.json()["items"]}
    assert "risk_halted" in reason_codes

    scheduler_jobs = client.get("/scheduler/jobs")
    assert scheduler_jobs.status_code == 200
    execution_jobs = [
        item for item in scheduler_jobs.json()["items"]
        if any(token in " ".join([
            str(item.get("job_id", "") or ""),
            str(item.get("job_name", "") or ""),
            str(item.get("mode", "") or ""),
        ]).lower() for token in ("cycle", "runtime", "orchestrator", "paper", "shadow", "rebalance"))
    ]
    assert execution_jobs
    assert all(bool(item.get("execution_blocked")) for item in execution_jobs)
    assert all(str(item.get("trading_state")).lower() == "halted" for item in execution_jobs)
