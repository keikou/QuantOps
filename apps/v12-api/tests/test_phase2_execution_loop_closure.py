from fastapi.testclient import TestClient

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app
from ai_hedge_bot.contracts.reason_codes import EXECUTION_DISABLED
from ai_hedge_bot.contracts.runtime_events import (
    CYCLE_COMPLETED,
    CYCLE_FAILED,
    CYCLE_STARTED,
    FILL_RECORDED,
    ORDER_BLOCKED,
    ORDER_SUBMITTED,
    PLANNER_GENERATED,
    PORTFOLIO_UPDATED,
)


client = TestClient(app)


def _reset_runtime_state() -> None:
    for table in [
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
    ]:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def test_phase2_successful_cycle_closes_execution_loop_into_truth_and_analytics() -> None:
    _reset_runtime_state()
    client.post("/runtime/resume")

    response = client.post("/runtime/run-once?mode=paper")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    run_id = payload["run_id"]

    bridge = client.get(f"/execution/bridge/by-run/{run_id}")
    assert bridge.status_code == 200
    bridge_payload = bridge.json()
    assert bridge_payload["status"] == "ok"
    assert bridge_payload["run_id"] == run_id
    assert bridge_payload["event_chain_complete"] is True
    assert bridge_payload["bridge_state"] == "filled"
    assert bridge_payload["planned_count"] >= 1
    assert bridge_payload["submitted_count"] >= 1
    assert bridge_payload["filled_count"] >= 1

    events = client.get(f"/runtime/events/by-run/{run_id}?limit=200")
    assert events.status_code == 200
    run_events = events.json()["items"]
    event_types = {item["event_type"] for item in run_events}
    assert {
        CYCLE_STARTED,
        PLANNER_GENERATED,
        ORDER_SUBMITTED,
        FILL_RECORDED,
        PORTFOLIO_UPDATED,
        CYCLE_COMPLETED,
    }.issubset(event_types)

    fills_payload = client.get("/execution/fills")
    assert fills_payload.status_code == 200
    run_fills = [item for item in fills_payload.json()["items"] if item.get("run_id") == run_id]
    assert len(run_fills) == bridge_payload["filled_count"]

    quality = client.get("/execution/quality/latest_summary")
    assert quality.status_code == 200
    quality_payload = quality.json()
    assert quality_payload["run_id"] == run_id
    assert quality_payload["fill_count"] == bridge_payload["filled_count"]
    assert quality_payload["order_count"] >= quality_payload["fill_count"]

    latest_position_count = CONTAINER.runtime_store.fetchone_dict(
        "SELECT COUNT(*) AS count FROM position_snapshots_latest"
    )
    latest_equity_count = CONTAINER.runtime_store.fetchone_dict(
        "SELECT COUNT(*) AS count FROM equity_snapshots"
    )
    assert int((latest_position_count or {}).get("count", 0) or 0) >= 1
    assert int((latest_equity_count or {}).get("count", 0) or 0) >= 1

    overview = client.get("/portfolio/overview")
    assert overview.status_code == 200
    overview_payload = overview.json()
    assert overview_payload["status"] == "ok"
    assert float(overview_payload["total_equity"]) > 0.0


def test_phase2_blocked_cycle_emits_explicit_block_reason_instead_of_silent_noop() -> None:
    _reset_runtime_state()
    client.post("/runtime/kill-switch")

    response = client.post("/runtime/run-once?mode=paper")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "blocked"
    assert payload["reason_code"] == EXECUTION_DISABLED
    run_id = payload["run_id"]

    events = client.get(f"/runtime/events/by-run/{run_id}?limit=50")
    assert events.status_code == 200
    run_events = events.json()["items"]
    event_types = {item["event_type"] for item in run_events}
    assert CYCLE_FAILED in event_types
    assert ORDER_BLOCKED in event_types or any(item.get("reason_code") == EXECUTION_DISABLED for item in run_events)

    blocked_event = next(item for item in run_events if item["event_type"] == CYCLE_FAILED)
    assert blocked_event["reason_code"] == EXECUTION_DISABLED
    assert blocked_event["details"]["trading_state"] == "halted"

    run_fills = CONTAINER.runtime_store.fetchone_dict(
        "SELECT COUNT(*) AS count FROM execution_fills WHERE run_id = ?",
        [run_id],
    )
    run_plans = CONTAINER.runtime_store.fetchone_dict(
        "SELECT COUNT(*) AS count FROM execution_plans WHERE run_id = ?",
        [run_id],
    )
    assert int((run_fills or {}).get("count", 0) or 0) == 0
    assert int((run_plans or {}).get("count", 0) or 0) == 0
