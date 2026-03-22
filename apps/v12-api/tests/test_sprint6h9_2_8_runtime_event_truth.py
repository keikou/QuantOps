from fastapi.testclient import TestClient
from unittest.mock import patch

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.app.main import app
from ai_hedge_bot.contracts.reason_codes import DEGRADED_MODE, EXECUTION_DISABLED, NO_POSITION_DELTA, ORDER_REJECTED, STALE_MARKET_DATA
from ai_hedge_bot.contracts.runtime_events import (
    CYCLE_COMPLETED,
    CYCLE_FAILED,
    CYCLE_STARTED,
    FILL_RECORDED,
    ORDER_BLOCKED,
    ORDER_SUBMITTED,
    PLANNER_GENERATED,
    PORTFOLIO_UPDATED,
    build_runtime_event,
)
from ai_hedge_bot.orchestrator.orchestration_service import OrchestrationService
from ai_hedge_bot.repositories.runtime_repository import RuntimeRepository

client = TestClient(app)


def _reset_runtime_tables() -> None:
    tables = [
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
        "equity_snapshots",
        "cash_ledger",
    ]
    for table in tables:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def test_runtime_events_capture_successful_cycle_truth() -> None:
    _reset_runtime_tables()
    client.post("/runtime/resume")

    response = client.post("/runtime/run-once?mode=paper")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    run_id = payload["run_id"]

    events = client.get("/runtime/events/latest?limit=200")
    assert events.status_code == 200
    items = events.json()["items"]
    run_events = [item for item in items if item.get("run_id") == run_id]
    event_types = {item["event_type"] for item in run_events}
    assert {
        CYCLE_STARTED,
        PLANNER_GENERATED,
        ORDER_SUBMITTED,
        FILL_RECORDED,
        PORTFOLIO_UPDATED,
        CYCLE_COMPLETED,
    }.issubset(event_types)
    for item in run_events:
        assert item["run_id"] == run_id
        assert item["cycle_id"]
        assert item["mode"] == "paper"
        assert item["timestamp"]
        assert item["source"]
        assert item["severity"]
        assert isinstance(item.get("details"), dict)


def test_runtime_reasons_capture_blocked_cycle_reason_code() -> None:
    _reset_runtime_tables()
    client.post("/runtime/kill-switch")

    response = client.post("/runtime/run-once?mode=paper")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "blocked"
    assert payload["reason_code"] == EXECUTION_DISABLED

    reasons = client.get("/runtime/reasons/latest?limit=50")
    assert reasons.status_code == 200
    items = reasons.json()["items"]
    blocked = next(item for item in items if item["event_type"] == CYCLE_FAILED and item["run_id"] == payload["run_id"])
    assert blocked["reason_code"] == EXECUTION_DISABLED
    assert blocked["status"] == "blocked"
    assert blocked["details"]["trading_state"] == "halted"


def test_runtime_repository_event_inserts_are_idempotent_and_filterable() -> None:
    _reset_runtime_tables()
    repo = RuntimeRepository()
    event = build_runtime_event(
        event_id="evt-fixed-1",
        event_type=ORDER_BLOCKED,
        run_id="run-fixed-1",
        cycle_id="cycle-fixed-1",
        mode="paper",
        source="test",
        status="blocked",
        severity="info",
        summary="No delta",
        reason_code=NO_POSITION_DELTA,
        symbol="BTCUSDT",
        details={"delta_qty": 0.0},
        timestamp="2026-03-23T00:00:00+00:00",
    )
    repo.create_event(event)
    repo.create_event(event)

    rows = repo.list_events(run_id="run-fixed-1", event_type=ORDER_BLOCKED, symbol="BTCUSDT", limit=10)
    assert len(rows) == 1
    assert rows[0]["reason_code"] == NO_POSITION_DELTA
    assert rows[0]["details"]["delta_qty"] == 0.0


def test_execution_bridge_emits_explicit_reason_when_no_decisions_exist() -> None:
    _reset_runtime_tables()
    service = OrchestrationService()
    result = {
        "run_id": "run-bridge-none",
        "cycle_id": "cycle-bridge-none",
        "timestamp": "2026-03-23T00:00:00+00:00",
    }

    payload = service._record_execution_runtime(result, "paper", [], [])
    assert payload["order_count"] == 0

    rows = RuntimeRepository().list_events(run_id="run-bridge-none", limit=20)
    planner_event = next(item for item in rows if item["event_type"] == PLANNER_GENERATED)
    blocked_event = next(item for item in rows if item["event_type"] == ORDER_BLOCKED)
    assert planner_event["status"] == "blocked"
    assert planner_event["reason_code"] == NO_POSITION_DELTA
    assert blocked_event["reason_code"] == NO_POSITION_DELTA
    assert blocked_event["details"]["blocking_component"] == "execution_bridge"


def test_execution_bridge_emits_explicit_reason_when_plans_submit_zero_orders() -> None:
    _reset_runtime_tables()
    service = OrchestrationService()
    result = {
        "run_id": "run-bridge-zero-orders",
        "cycle_id": "cycle-bridge-zero-orders",
        "timestamp": "2026-03-23T00:00:00+00:00",
    }
    decisions = [{
        "symbol": "BTCUSDT",
        "side": "long",
        "target_weight": 0.15,
        "alpha_family": "trend",
    }]
    fake_plan = {
        "algo": "twap",
        "route": "maker_bias",
        "urgency": "normal",
        "participation_rate": 0.05,
        "expire_seconds": 60,
        "slice_count": 1,
        "child_orders": [{"child_index": 1, "child_qty": 0.0, "style": "twap", "time_bucket_sec": 0, "route": "maker_bias"}],
        "spread_bps": 2.0,
        "notional_usd": 1000.0,
        "quote_age_sec": 0.0,
        "mode": "paper",
        "stale_quote": False,
        "decision_price": 100.0,
        "price_drift_bps": 12.0,
        "expiry_policy": {"time_expiry_at_sec": 60, "decision_price": 100.0, "price_drift_bps": 12.0},
        "observed_volume_qty": 100.0,
        "volume_participation": 0.01,
        "pov_fallback": False,
        "routing_candidates": [],
        "routing_fallback": False,
        "required_margin": 1000.0,
        "available_margin": 100000.0,
        "margin_limited": False,
    }
    market_prices = [{
        "symbol": "BTCUSDT",
        "bid": 99.9,
        "ask": 100.1,
        "mid": 100.0,
        "quote_age_sec": 0.0,
        "source": "test_quote",
        "quote_time": "2026-03-23T00:00:00+00:00",
    }]
    with patch.object(service._planner, "build_plan", return_value=fake_plan):
        payload = service._record_execution_runtime(result, "paper", decisions, market_prices)

    assert payload["order_count"] == 0
    rows = RuntimeRepository().list_events(run_id="run-bridge-zero-orders", limit=20)
    planner_event = next(item for item in rows if item["event_type"] == PLANNER_GENERATED)
    blocked_event = next(
        item
        for item in rows
        if item["event_type"] == ORDER_BLOCKED
        and item["details"]["blocking_component"] == "execution_bridge"
        and item["summary"] == "Execution bridge produced zero child orders for generated plans."
    )
    assert planner_event["status"] == "blocked"
    assert blocked_event["reason_code"] == DEGRADED_MODE
    assert blocked_event["details"]["plan_count"] == 1


def test_execution_bridge_endpoint_explains_no_decision_cycle() -> None:
    _reset_runtime_tables()
    service = OrchestrationService()
    result = {
        "run_id": "run-bridge-endpoint-none",
        "cycle_id": "cycle-bridge-endpoint-none",
        "timestamp": "2026-03-23T00:00:00+00:00",
    }
    service._record_execution_runtime(result, "paper", [], [])

    bridge = client.get("/execution/bridge/by-run/run-bridge-endpoint-none")
    assert bridge.status_code == 200
    bridge_payload = bridge.json()
    assert bridge_payload["bridge_state"] == "no_decision"
    assert bridge_payload["zero_submit_reason_code"] == NO_POSITION_DELTA

    planner = client.get("/execution/plans/by-run/run-bridge-endpoint-none")
    assert planner.status_code == 200
    planner_payload = planner.json()
    assert planner_payload["planner_status"] == "blocked"
    assert planner_payload["reason_code"] == NO_POSITION_DELTA
    assert planner_payload["items"] == []


def test_execution_bridge_endpoint_explains_planned_not_submitted_cycle() -> None:
    _reset_runtime_tables()
    service = OrchestrationService()
    result = {
        "run_id": "run-bridge-endpoint-zero-orders",
        "cycle_id": "cycle-bridge-endpoint-zero-orders",
        "timestamp": "2026-03-23T00:00:00+00:00",
    }
    decisions = [{
        "symbol": "BTCUSDT",
        "side": "long",
        "target_weight": 0.15,
        "alpha_family": "trend",
    }]
    fake_plan = {
        "algo": "twap",
        "route": "maker_bias",
        "urgency": "normal",
        "participation_rate": 0.05,
        "expire_seconds": 60,
        "slice_count": 1,
        "child_orders": [{"child_index": 1, "child_qty": 0.0, "style": "twap", "time_bucket_sec": 0, "route": "maker_bias"}],
        "spread_bps": 2.0,
        "notional_usd": 1000.0,
        "quote_age_sec": 0.0,
        "mode": "paper",
        "stale_quote": False,
        "decision_price": 100.0,
        "price_drift_bps": 12.0,
        "expiry_policy": {"time_expiry_at_sec": 60, "decision_price": 100.0, "price_drift_bps": 12.0},
        "observed_volume_qty": 100.0,
        "volume_participation": 0.01,
        "pov_fallback": False,
        "routing_candidates": [],
        "routing_fallback": False,
        "required_margin": 1000.0,
        "available_margin": 100000.0,
        "margin_limited": False,
    }
    market_prices = [{
        "symbol": "BTCUSDT",
        "bid": 99.9,
        "ask": 100.1,
        "mid": 100.0,
        "quote_age_sec": 0.0,
        "source": "test_quote",
        "quote_time": "2026-03-23T00:00:00+00:00",
    }]
    with patch.object(service._planner, "build_plan", return_value=fake_plan):
        service._record_execution_runtime(result, "paper", decisions, market_prices)

    bridge = client.get("/execution/bridge/by-run/run-bridge-endpoint-zero-orders")
    assert bridge.status_code == 200
    bridge_payload = bridge.json()
    assert bridge_payload["bridge_state"] == "planned_blocked"
    assert bridge_payload["blocking_component"] == "execution_bridge"
    assert bridge_payload["planned_count"] == 1
    assert bridge_payload["submitted_count"] == 0

    planner = client.get("/execution/plans/by-run/run-bridge-endpoint-zero-orders")
    assert planner.status_code == 200
    planner_payload = planner.json()
    assert planner_payload["planner_status"] == "blocked"
    assert planner_payload["items"][0]["symbol"] == "BTCUSDT"
    assert planner_payload["items"][0]["has_child_orders"] is False
    assert planner_payload["items"][0]["block_reason_code"] == DEGRADED_MODE


def test_execution_bridge_captures_stale_price_degradation_reason() -> None:
    _reset_runtime_tables()
    service = OrchestrationService()
    result = {
        "run_id": "run-bridge-stale-price",
        "cycle_id": "cycle-bridge-stale-price",
        "timestamp": "2026-03-23T00:00:00+00:00",
    }
    decisions = [{
        "symbol": "BTCUSDT",
        "side": "long",
        "target_weight": 0.15,
        "alpha_family": "trend",
    }]
    fake_plan = {
        "algo": "twap",
        "route": "taker_primary",
        "urgency": "aggressive",
        "participation_rate": 0.05,
        "expire_seconds": 15,
        "slice_count": 1,
        "child_orders": [{"child_index": 1, "child_qty": 10.0, "style": "twap", "time_bucket_sec": 0, "route": "taker_primary"}],
        "spread_bps": 2.0,
        "notional_usd": 1000.0,
        "quote_age_sec": 25.0,
        "mode": "paper",
        "stale_quote": True,
        "decision_price": 100.0,
        "price_drift_bps": 12.0,
        "expiry_policy": {"time_expiry_at_sec": 15, "decision_price": 100.0, "price_drift_bps": 12.0},
        "observed_volume_qty": 100.0,
        "volume_participation": 0.1,
        "pov_fallback": False,
        "routing_candidates": [],
        "routing_fallback": True,
        "required_margin": 1000.0,
        "available_margin": 100000.0,
        "margin_limited": False,
    }
    market_prices = [{
        "symbol": "BTCUSDT",
        "bid": 99.9,
        "ask": 100.1,
        "mid": 100.0,
        "quote_age_sec": 25.0,
        "source": "test_quote",
        "quote_time": "2026-03-23T00:00:00+00:00",
    }]
    with patch.object(service._planner, "build_plan", return_value=fake_plan):
        service._record_execution_runtime(result, "paper", decisions, market_prices)

    rows = RuntimeRepository().list_events(run_id="run-bridge-stale-price", limit=20)
    stale_event = next(item for item in rows if item["reason_code"] == STALE_MARKET_DATA)
    assert stale_event["details"]["blocking_component"] == "execution_planner"

    planner = client.get("/execution/plans/by-run/run-bridge-stale-price").json()
    assert planner["items"][0]["price_snapshot_status"] == "stale"


def test_execution_bridge_captures_submitted_no_fill_reason() -> None:
    _reset_runtime_tables()
    service = OrchestrationService()
    result = {
        "run_id": "run-bridge-no-fill",
        "cycle_id": "cycle-bridge-no-fill",
        "timestamp": "2026-03-23T00:00:00+00:00",
    }
    decisions = [{
        "symbol": "BTCUSDT",
        "side": "long",
        "target_weight": 0.15,
        "alpha_family": "trend",
    }]
    fake_plan = {
        "algo": "twap",
        "route": "maker_bias",
        "urgency": "normal",
        "participation_rate": 0.05,
        "expire_seconds": 60,
        "slice_count": 1,
        "child_orders": [{"child_index": 1, "child_qty": 10.0, "style": "twap", "time_bucket_sec": 0, "route": "maker_bias"}],
        "spread_bps": 2.0,
        "notional_usd": 1000.0,
        "quote_age_sec": 25.0,
        "mode": "paper",
        "stale_quote": True,
        "decision_price": 100.0,
        "price_drift_bps": 12.0,
        "expiry_policy": {"time_expiry_at_sec": 60, "decision_price": 100.0, "price_drift_bps": 12.0},
        "observed_volume_qty": 100.0,
        "volume_participation": 0.1,
        "pov_fallback": False,
        "routing_candidates": [],
        "routing_fallback": False,
        "required_margin": 1000.0,
        "available_margin": 100000.0,
        "margin_limited": False,
    }
    market_prices = [{
        "symbol": "BTCUSDT",
        "bid": 99.9,
        "ask": 100.1,
        "mid": 100.0,
        "quote_age_sec": 25.0,
        "source": "test_quote",
        "quote_time": "2026-03-23T00:00:00+00:00",
    }]
    with patch.object(service._planner, "build_plan", return_value=fake_plan):
        service._record_execution_runtime(result, "paper", decisions, market_prices)

    bridge = client.get("/execution/bridge/by-run/run-bridge-no-fill").json()
    assert bridge["bridge_state"] == "submitted_no_fill"
    assert bridge["latest_reason_code"] == ORDER_REJECTED
    assert bridge["submitted_count"] >= 1
    assert bridge["filled_count"] == 0
