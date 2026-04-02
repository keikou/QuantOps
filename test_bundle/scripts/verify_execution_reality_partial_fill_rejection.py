from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Execution_reality_packet02_partial_fill_rejection_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def _reset_runtime_state(container, execution_routes) -> None:
    execution_routes._execution_view_cache["expires_at"] = None
    execution_routes._execution_view_cache["key"] = None
    execution_routes._execution_view_cache["payload"] = None
    for table in [
        "runtime_control_state",
        "execution_plans",
        "execution_fills",
        "execution_orders",
        "execution_quality_snapshots",
        "execution_state_snapshots",
        "execution_block_reasons",
    ]:
        try:
            container.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_packet02_plan_doc")
    else:
        plan_text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "partial-fill and rejection states are visible and attributable",
            "/execution/orders",
            "/execution/fills",
            "/execution/state/latest",
        ]:
            if needle not in plan_text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.app.container import CONTAINER
    from ai_hedge_bot.app.main import app
    from ai_hedge_bot.api.routes import execution as execution_routes

    client = TestClient(app)
    _reset_runtime_state(CONTAINER, execution_routes)

    now = datetime.now(timezone.utc)
    run_id = "run-exec-visibility-1"
    partial_plan_id = "plan-partial-1"
    rejected_plan_id = "plan-rejected-1"
    partial_order_id = "order-partial-1"
    rejected_order_id = "order-rejected-1"

    CONTAINER.runtime_store.append(
        "execution_plans",
        [
            {
                "plan_id": partial_plan_id,
                "created_at": now.isoformat(),
                "run_id": run_id,
                "mode": "paper",
                "symbol": "BTCUSDT",
                "side": "buy",
                "target_weight": 0.1,
                "order_qty": 2.0,
                "limit_price": 100.0,
                "participation_rate": 0.1,
                "status": "planned",
                "algo": "twap",
                "route": "primary",
                "expire_seconds": 120,
                "slice_count": 1,
                "metadata_json": "{}",
            },
            {
                "plan_id": rejected_plan_id,
                "created_at": (now + timedelta(seconds=1)).isoformat(),
                "run_id": run_id,
                "mode": "paper",
                "symbol": "ETHUSDT",
                "side": "sell",
                "target_weight": 0.05,
                "order_qty": 1.0,
                "limit_price": 200.0,
                "participation_rate": 0.1,
                "status": "planned",
                "algo": "twap",
                "route": "primary",
                "expire_seconds": 120,
                "slice_count": 1,
                "metadata_json": "{}",
            },
        ],
    )

    CONTAINER.runtime_store.append(
        "execution_orders",
        [
            {
                "order_id": partial_order_id,
                "plan_id": partial_plan_id,
                "parent_order_id": None,
                "client_order_id": "client-partial-1",
                "strategy_id": "strategy-1",
                "alpha_family": "trend",
                "symbol": "BTCUSDT",
                "side": "buy",
                "order_type": "limit",
                "qty": 2.0,
                "limit_price": 100.0,
                "venue": "paper",
                "route": "primary",
                "algo": "twap",
                "submit_time": (now + timedelta(seconds=2)).isoformat(),
                "status": "partially_filled",
                "source": "planner",
                "metadata_json": json.dumps({"filled_qty": 1.0, "remaining_qty": 1.0}),
                "created_at": (now + timedelta(seconds=2)).isoformat(),
                "updated_at": (now + timedelta(seconds=4)).isoformat(),
            },
            {
                "order_id": rejected_order_id,
                "plan_id": rejected_plan_id,
                "parent_order_id": None,
                "client_order_id": "client-rejected-1",
                "strategy_id": "strategy-2",
                "alpha_family": "mean_reversion",
                "symbol": "ETHUSDT",
                "side": "sell",
                "order_type": "limit",
                "qty": 1.0,
                "limit_price": 200.0,
                "venue": "paper",
                "route": "primary",
                "algo": "twap",
                "submit_time": (now + timedelta(seconds=3)).isoformat(),
                "status": "rejected",
                "source": "planner",
                "metadata_json": json.dumps({"reject_reason": "risk_guard"}),
                "created_at": (now + timedelta(seconds=3)).isoformat(),
                "updated_at": (now + timedelta(seconds=5)).isoformat(),
            },
        ],
    )

    CONTAINER.runtime_store.append(
        "execution_fills",
        {
            "fill_id": "fill-partial-1",
            "created_at": (now + timedelta(seconds=4)).isoformat(),
            "run_id": run_id,
            "mode": "paper",
            "plan_id": partial_plan_id,
            "order_id": partial_order_id,
            "client_order_id": "client-partial-1",
            "strategy_id": "strategy-1",
            "alpha_family": "trend",
            "symbol": "BTCUSDT",
            "side": "buy",
            "fill_qty": 1.0,
            "fill_price": 100.2,
            "slippage_bps": 2.0,
            "latency_ms": 42.0,
            "fee_bps": 0.1,
            "bid": 100.1,
            "ask": 100.3,
            "arrival_mid_price": 100.2,
            "price_source": "test",
            "quote_time": (now + timedelta(seconds=4)).isoformat(),
            "quote_age_sec": 0.1,
            "fallback_reason": None,
            "status": "filled",
        },
    )

    orders_payload = client.get("/execution/orders").json()
    fills_payload = client.get("/execution/fills").json()
    state_payload = client.get("/execution/state/latest").json()

    orders = orders_payload.get("items", [])
    fills = fills_payload.get("items", [])

    partial_order = next((row for row in orders if row.get("order_id") == partial_order_id), None)
    rejected_order = next((row for row in orders if row.get("order_id") == rejected_order_id), None)
    partial_fill = next((row for row in fills if row.get("order_id") == partial_order_id), None)

    if partial_order is None:
        failures.append("missing_partial_order")
    elif partial_order.get("status") != "partially_filled":
        failures.append("partial_order_status_not_visible")

    if rejected_order is None:
        failures.append("missing_rejected_order")
    elif rejected_order.get("status") != "rejected":
        failures.append("rejected_order_status_not_visible")

    if partial_fill is None:
        failures.append("missing_partial_fill")
    else:
        if partial_fill.get("plan_id") != partial_plan_id:
            failures.append("partial_fill_plan_link_missing")

    if state_payload.get("status") != "ok":
        failures.append("state_payload_not_ok")
    else:
        if int(state_payload.get("open_order_count", 0) or 0) < 1:
            failures.append("open_order_count_missing_partial_visibility")
        if int(state_payload.get("submitted_order_count", 0) or 0) < 1:
            failures.append("submitted_order_count_missing_partial_visibility")
        # rejected order should not inflate submitted count beyond the one partial order
        if int(state_payload.get("submitted_order_count", 0) or 0) > 1:
            failures.append("rejected_order_counted_as_submitted")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
