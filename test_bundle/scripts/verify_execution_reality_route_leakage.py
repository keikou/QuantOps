from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Execution_reality_packet10_route_leakage_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def _reset_runtime_state(container, execution_routes) -> None:
    execution_routes._execution_quality_summary_cache["expires_at"] = None
    execution_routes._execution_quality_summary_cache["payload"] = None
    for table in [
        "execution_quality_snapshots",
        "execution_fills",
        "execution_plans",
        "shadow_pnl_snapshots",
    ]:
        try:
            container.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_packet10_plan_doc")
    else:
        plan_text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/execution/quality/route-leakage/latest",
            "per-route execution leakage attribution is explicit for the latest run",
            "route `notional_share` sums to `1.0`",
            "route `execution_drag_usd` sums to latest run `execution_drag_usd`",
        ]:
            if needle not in plan_text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.app.container import CONTAINER
    from ai_hedge_bot.app.main import app
    from ai_hedge_bot.api.routes import execution as execution_routes

    client = TestClient(app)
    _reset_runtime_state(CONTAINER, execution_routes)

    now = datetime.now(timezone.utc)
    run_id = "run-route-leak-10"
    CONTAINER.runtime_store.append(
        "execution_quality_snapshots",
        {
            "snapshot_id": "snap-route-leak-10",
            "created_at": (now + timedelta(seconds=2)).isoformat(),
            "run_id": run_id,
            "cycle_id": "cycle-route-leak-10",
            "mode": "shadow",
            "order_count": 3,
            "fill_count": 3,
            "fill_rate": 1.0,
            "avg_slippage_bps": 3.0,
            "latency_ms_p50": 20.0,
            "latency_ms_p95": 40.0,
        },
    )
    CONTAINER.runtime_store.append(
        "shadow_pnl_snapshots",
        {
            "run_id": run_id,
            "created_at": (now + timedelta(seconds=3)).isoformat(),
            "gross_alpha_pnl_usd": 100.0,
            "net_shadow_pnl_usd": 88.0,
            "execution_drag_usd": 12.0,
            "slippage_drag_usd": 5.0,
            "fee_drag_usd": 4.0,
            "latency_drag_usd": 3.0,
        },
    )
    CONTAINER.runtime_store.append(
        "execution_plans",
        [
            {
                "plan_id": "plan-maker-10",
                "created_at": (now + timedelta(seconds=2)).isoformat(),
                "run_id": run_id,
                "mode": "shadow",
                "symbol": "BTCUSDT",
                "side": "buy",
                "target_weight": 0.1,
                "order_qty": 1.0,
                "limit_price": 200.0,
                "participation_rate": 0.1,
                "status": "planned",
                "algo": "twap",
                "route": "maker_bias",
                "expire_seconds": 120,
                "slice_count": 1,
                "metadata_json": "{}",
            },
            {
                "plan_id": "plan-taker-10",
                "created_at": (now + timedelta(seconds=2)).isoformat(),
                "run_id": run_id,
                "mode": "shadow",
                "symbol": "ETHUSDT",
                "side": "buy",
                "target_weight": 0.1,
                "order_qty": 1.0,
                "limit_price": 300.0,
                "participation_rate": 0.1,
                "status": "planned",
                "algo": "twap",
                "route": "taker_primary",
                "expire_seconds": 120,
                "slice_count": 1,
                "metadata_json": "{}",
            },
        ],
    )
    CONTAINER.runtime_store.append(
        "execution_fills",
        [
            {
                "fill_id": "fill-maker-10",
                "created_at": (now + timedelta(seconds=3)).isoformat(),
                "run_id": run_id,
                "mode": "shadow",
                "plan_id": "plan-maker-10",
                "order_id": "order-maker-10",
                "client_order_id": "client-maker-10",
                "strategy_id": "strategy-10",
                "alpha_family": "trend",
                "symbol": "BTCUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 200.0,
                "slippage_bps": 2.0,
                "latency_ms": 15.0,
                "fee_bps": 1.0,
                "bid": 199.9,
                "ask": 200.1,
                "arrival_mid_price": 200.0,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=3)).isoformat(),
                "quote_age_sec": 0.1,
                "fallback_reason": None,
                "status": "filled",
            },
            {
                "fill_id": "fill-taker-10",
                "created_at": (now + timedelta(seconds=4)).isoformat(),
                "run_id": run_id,
                "mode": "shadow",
                "plan_id": "plan-taker-10",
                "order_id": "order-taker-10",
                "client_order_id": "client-taker-10",
                "strategy_id": "strategy-10",
                "alpha_family": "trend",
                "symbol": "ETHUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 300.0,
                "slippage_bps": 4.0,
                "latency_ms": 25.0,
                "fee_bps": 2.0,
                "bid": 299.9,
                "ask": 300.1,
                "arrival_mid_price": 300.0,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=4)).isoformat(),
                "quote_age_sec": 0.1,
                "fallback_reason": None,
                "status": "filled",
            },
        ],
    )

    payload = client.get("/execution/quality/route-leakage/latest").json()

    for key in ["run_id", "mode", "items", "totals"]:
        if key not in payload:
            failures.append(f"payload_missing:{key}")
    if payload.get("run_id") != run_id:
        failures.append("run_id_mismatch")
    if payload.get("mode") != "shadow":
        failures.append("mode_mismatch")

    items = payload.get("items", [])
    if len(items) != 2:
        failures.append("route_row_count_mismatch")

    by_route = {str(item.get("route") or ""): item for item in items}
    for route in ["maker_bias", "taker_primary"]:
        item = by_route.get(route)
        if item is None:
            failures.append(f"missing_route:{route}")
            continue
        for key in [
            "fill_count",
            "gross_notional_usd",
            "notional_share",
            "avg_slippage_bps",
            "avg_latency_ms",
            "avg_fee_bps",
            "slippage_drag_usd",
            "fee_drag_usd",
            "latency_drag_usd",
            "execution_drag_usd",
        ]:
            if key not in item:
                failures.append(f"{route}_missing:{key}")

    share_sum = sum(float(item.get("notional_share", 0.0) or 0.0) for item in items)
    execution_drag_sum = sum(float(item.get("execution_drag_usd", 0.0) or 0.0) for item in items)
    if abs(share_sum - 1.0) > 1e-9:
        failures.append("share_sum_invalid")
    if abs(execution_drag_sum - float((payload.get("totals") or {}).get("execution_drag_usd", 0.0) or 0.0)) > 1e-9:
        failures.append("execution_drag_sum_invalid")

    maker = by_route.get("maker_bias", {})
    taker = by_route.get("taker_primary", {})
    if float(maker.get("gross_notional_usd", 0.0) or 0.0) >= float(taker.get("gross_notional_usd", 0.0) or 0.0):
        failures.append("route_notional_order_invalid")
    if float(maker.get("execution_drag_usd", 0.0) or 0.0) >= float(taker.get("execution_drag_usd", 0.0) or 0.0):
        failures.append("route_drag_order_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
