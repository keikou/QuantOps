from __future__ import annotations

from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app


client = TestClient(app)


def _reset_phase5_state() -> None:
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


def test_phase5_close1_risk_breach_triggers_execution_suppression() -> None:
    _reset_phase5_state()
    client.post("/runtime/resume")

    # Seed one in-flight order so the kill-switch path has something to drain.
    CONTAINER.runtime_store.append(
        "execution_orders",
        {
            "order_id": "phase5-order-1",
            "plan_id": "phase5-plan-1",
            "parent_order_id": "phase5-plan-1",
            "client_order_id": "phase5-client-1",
            "strategy_id": "test",
            "alpha_family": "runtime",
            "symbol": "BTCUSDT",
            "side": "buy",
            "order_type": "limit",
            "qty": 1.0,
            "limit_price": 100000.0,
            "venue": "paper_simulator",
            "route": "maker_bias",
            "algo": "twap",
            "submit_time": "2026-03-29T00:00:00Z",
            "status": "submitted",
            "source": "test",
            "metadata_json": "{}",
            "created_at": "2026-03-29T00:00:00Z",
            "updated_at": "2026-03-29T00:00:00Z",
        },
    )

    plans_before = _count("execution_plans")
    orders_before = _count("execution_orders")
    fills_before = _count("execution_fills")

    # Treat kill-switch as the explicit risk-breach trigger for the first closure packet.
    kill = client.post("/runtime/kill-switch")
    assert kill.status_code == 200
    kill_body = kill.json()
    assert kill_body["status"] == "ok"
    assert kill_body["trading_state"] == "halted"
    assert kill_body["cancelled_open_orders"] == 1

    # Once halted, no new execution should be created by the runtime cycle.
    blocked = client.post("/runtime/run-once?mode=paper")
    assert blocked.status_code == 200
    blocked_body = blocked.json()
    assert blocked_body["status"] == "blocked"
    assert blocked_body["trading_state"] == "halted"
    assert blocked_body["reason_code"] == "execution_disabled"

    plans_after = _count("execution_plans")
    orders_after = _count("execution_orders")
    fills_after = _count("execution_fills")

    assert plans_after == plans_before
    assert orders_after == orders_before
    assert fills_after == fills_before

    latest_state = client.get("/execution/state/latest")
    assert latest_state.status_code == 200
    latest_state_body = latest_state.json()
    assert str(latest_state_body["trading_state"]).lower() == "halted"
    assert str(latest_state_body["execution_state"]).lower() in {"halted", "blocked"}
    assert latest_state_body["open_order_count"] == 0

    latest_reasons = client.get("/execution/block-reasons/latest")
    assert latest_reasons.status_code == 200
    reason_items = latest_reasons.json()["items"]
    assert reason_items
    assert reason_items[0]["code"] == "risk_halted"

    runtime_reasons = client.get(f"/runtime/reasons/by-run/{blocked_body['run_id']}")
    assert runtime_reasons.status_code == 200
    runtime_reason_items = runtime_reasons.json()["items"]
    assert runtime_reason_items
    assert runtime_reason_items[0]["reason_code"] == "execution_disabled"
    assert runtime_reason_items[0]["status"] == "blocked"

    audit_rows = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT event_type, payload_json
        FROM audit_logs
        WHERE category = 'runtime'
        ORDER BY created_at DESC
        LIMIT 5
        """
    )
    assert audit_rows
    assert any(str(row["event_type"]) == "kill_switch" for row in audit_rows)
