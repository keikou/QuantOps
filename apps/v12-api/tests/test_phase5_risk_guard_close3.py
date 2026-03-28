from __future__ import annotations

from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app


client = TestClient(app)


def _reset_phase5_close3_state() -> None:
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
    ]
    for table in tables:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def _count(table: str) -> int:
    row = CONTAINER.runtime_store.fetchone_dict(f"SELECT COUNT(*) AS c FROM {table}") or {"c": 0}
    return int(row.get("c") or 0)


def test_phase5_close3_only_valid_recovery_can_resume_execution() -> None:
    _reset_phase5_close3_state()
    client.post("/runtime/resume")

    kill = client.post("/runtime/kill-switch")
    assert kill.status_code == 200
    assert kill.json()["trading_state"] == "halted"

    blocked = client.post("/runtime/run-once?mode=paper")
    assert blocked.status_code == 200
    blocked_body = blocked.json()
    assert blocked_body["status"] == "blocked"
    assert blocked_body["reason_code"] == "execution_disabled"

    counts_before_resume = {
        "rebalance_plans": _count("rebalance_plans"),
        "execution_plans": _count("execution_plans"),
        "execution_orders": _count("execution_orders"),
        "execution_fills": _count("execution_fills"),
    }

    resume = client.post("/runtime/resume")
    assert resume.status_code == 200
    resume_body = resume.json()
    assert resume_body["status"] == "ok"
    assert resume_body["trading_state"] == "running"

    resumed_cycle = client.post("/runtime/run-once?mode=paper")
    assert resumed_cycle.status_code == 200
    resumed_body = resumed_cycle.json()
    assert resumed_body["status"] == "ok"
    assert resumed_body["result"]["status"] == "ok"

    counts_after_resume = {
        "rebalance_plans": _count("rebalance_plans"),
        "execution_plans": _count("execution_plans"),
        "execution_orders": _count("execution_orders"),
        "execution_fills": _count("execution_fills"),
    }
    assert counts_after_resume["rebalance_plans"] > counts_before_resume["rebalance_plans"]
    assert counts_after_resume["execution_plans"] > counts_before_resume["execution_plans"]
    assert counts_after_resume["execution_orders"] > counts_before_resume["execution_orders"]
    assert counts_after_resume["execution_fills"] > counts_before_resume["execution_fills"]

    trading_state = client.get("/runtime/trading-state")
    assert trading_state.status_code == 200
    assert trading_state.json()["trading_state"] == "running"

    latest_state = client.get("/execution/state/latest")
    assert latest_state.status_code == 200
    latest_state_body = latest_state.json()
    assert str(latest_state_body["trading_state"]).lower() == "running"
    assert str(latest_state_body["execution_state"]).lower() not in {"halted", "blocked"}
    assert latest_state_body["active_plan_count"] >= 1

    runtime_reasons = client.get(f"/runtime/reasons/by-run/{blocked_body['run_id']}")
    assert runtime_reasons.status_code == 200
    blocked_items = runtime_reasons.json()["items"]
    assert blocked_items
    assert blocked_items[0]["reason_code"] == "execution_disabled"

    audit_rows = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT event_type, payload_json
        FROM audit_logs
        WHERE category = 'runtime'
        ORDER BY created_at DESC
        LIMIT 10
        """
    )
    event_types = [str(row["event_type"]) for row in audit_rows]
    assert "kill_switch" in event_types
    assert "resume" in event_types
    assert "run_finished" in event_types
