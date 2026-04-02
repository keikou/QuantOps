from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Execution_reality_packet06_latency_mode_route_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def _reset_runtime_state(container, execution_routes) -> None:
    execution_routes._execution_quality_summary_cache["expires_at"] = None
    execution_routes._execution_quality_summary_cache["payload"] = None
    for table in [
        "execution_fills",
        "execution_plans",
        "execution_quality_snapshots",
    ]:
        try:
            container.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_packet06_plan_doc")
    else:
        plan_text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/execution/quality/latency-by-mode-route",
            "explicit by mode and execution route",
            "latency evidence from different routes remains separated",
            "latency_ms_p95 >= latency_ms_p50",
        ]:
            if needle not in plan_text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.app.container import CONTAINER
    from ai_hedge_bot.app.main import app
    from ai_hedge_bot.api.routes import execution as execution_routes

    client = TestClient(app)
    _reset_runtime_state(CONTAINER, execution_routes)

    now = datetime.now(timezone.utc)
    CONTAINER.runtime_store.append(
        "execution_quality_snapshots",
        [
            {
                "snapshot_id": "snap-paper-06",
                "created_at": (now + timedelta(seconds=3)).isoformat(),
                "run_id": "run-paper-06",
                "cycle_id": "cycle-paper-06",
                "mode": "paper",
                "order_count": 3,
                "fill_count": 3,
                "fill_rate": 1.0,
                "avg_slippage_bps": 1.5,
                "latency_ms_p50": 20.0,
                "latency_ms_p95": 45.0,
            },
            {
                "snapshot_id": "snap-shadow-06",
                "created_at": (now + timedelta(seconds=6)).isoformat(),
                "run_id": "run-shadow-06",
                "cycle_id": "cycle-shadow-06",
                "mode": "shadow",
                "order_count": 2,
                "fill_count": 2,
                "fill_rate": 1.0,
                "avg_slippage_bps": 3.8,
                "latency_ms_p50": 35.0,
                "latency_ms_p95": 70.0,
            },
        ],
    )

    CONTAINER.runtime_store.append(
        "execution_plans",
        [
            {
                "plan_id": "plan-paper-maker",
                "created_at": (now + timedelta(seconds=3)).isoformat(),
                "run_id": "run-paper-06",
                "mode": "paper",
                "symbol": "BTCUSDT",
                "side": "buy",
                "target_weight": 0.1,
                "order_qty": 1.0,
                "limit_price": 100.0,
                "participation_rate": 0.2,
                "status": "planned",
                "algo": "twap",
                "route": "maker_bias",
                "expire_seconds": 120,
                "slice_count": 1,
                "metadata_json": "{}",
            },
            {
                "plan_id": "plan-paper-taker",
                "created_at": (now + timedelta(seconds=4)).isoformat(),
                "run_id": "run-paper-06",
                "mode": "paper",
                "symbol": "ETHUSDT",
                "side": "sell",
                "target_weight": 0.05,
                "order_qty": 1.0,
                "limit_price": 200.0,
                "participation_rate": 0.2,
                "status": "planned",
                "algo": "twap",
                "route": "taker_primary",
                "expire_seconds": 120,
                "slice_count": 1,
                "metadata_json": "{}",
            },
            {
                "plan_id": "plan-shadow-maker",
                "created_at": (now + timedelta(seconds=6)).isoformat(),
                "run_id": "run-shadow-06",
                "mode": "shadow",
                "symbol": "SOLUSDT",
                "side": "buy",
                "target_weight": 0.08,
                "order_qty": 2.0,
                "limit_price": 50.0,
                "participation_rate": 0.2,
                "status": "planned",
                "algo": "twap",
                "route": "maker_bias",
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
                "fill_id": "fill-paper-maker-1",
                "created_at": (now + timedelta(seconds=3)).isoformat(),
                "run_id": "run-paper-06",
                "mode": "paper",
                "plan_id": "plan-paper-maker",
                "order_id": "order-paper-maker-1",
                "client_order_id": "client-paper-maker-1",
                "strategy_id": "strategy-paper",
                "alpha_family": "trend",
                "symbol": "BTCUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 100.1,
                "slippage_bps": 1.0,
                "latency_ms": 15.0,
                "fee_bps": 0.1,
                "bid": 100.0,
                "ask": 100.2,
                "arrival_mid_price": 100.1,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=3)).isoformat(),
                "quote_age_sec": 0.1,
                "fallback_reason": None,
                "status": "filled",
            },
            {
                "fill_id": "fill-paper-taker-1",
                "created_at": (now + timedelta(seconds=4)).isoformat(),
                "run_id": "run-paper-06",
                "mode": "paper",
                "plan_id": "plan-paper-taker",
                "order_id": "order-paper-taker-1",
                "client_order_id": "client-paper-taker-1",
                "strategy_id": "strategy-paper",
                "alpha_family": "trend",
                "symbol": "ETHUSDT",
                "side": "sell",
                "fill_qty": 1.0,
                "fill_price": 199.8,
                "slippage_bps": 2.0,
                "latency_ms": 45.0,
                "fee_bps": 0.1,
                "bid": 199.7,
                "ask": 199.9,
                "arrival_mid_price": 199.8,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=4)).isoformat(),
                "quote_age_sec": 0.1,
                "fallback_reason": None,
                "status": "filled",
            },
            {
                "fill_id": "fill-shadow-maker-1",
                "created_at": (now + timedelta(seconds=6)).isoformat(),
                "run_id": "run-shadow-06",
                "mode": "shadow",
                "plan_id": "plan-shadow-maker",
                "order_id": "order-shadow-maker-1",
                "client_order_id": "client-shadow-maker-1",
                "strategy_id": "strategy-shadow",
                "alpha_family": "mean_reversion",
                "symbol": "SOLUSDT",
                "side": "buy",
                "fill_qty": 2.0,
                "fill_price": 50.1,
                "slippage_bps": 4.0,
                "latency_ms": 60.0,
                "fee_bps": 0.1,
                "bid": 50.0,
                "ask": 50.2,
                "arrival_mid_price": 50.1,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=6)).isoformat(),
                "quote_age_sec": 0.1,
                "fallback_reason": None,
                "status": "filled",
            },
        ],
    )

    payload = client.get("/execution/quality/latency-by-mode-route").json()

    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    items = payload.get("items", [])
    if len(items) < 3:
        failures.append("insufficient_latency_rows")

    expected_keys = {
        ("paper", "maker_bias"),
        ("paper", "taker_primary"),
        ("shadow", "maker_bias"),
    }
    actual_keys = {(str(item.get("mode") or ""), str(item.get("route") or "")) for item in items}
    for key in expected_keys:
        if key not in actual_keys:
            failures.append(f"missing_row:{key[0]}:{key[1]}")

    for item in items:
        for key in [
            "run_id",
            "cycle_id",
            "mode",
            "route",
            "fill_count",
            "avg_latency_ms",
            "latency_ms_p50",
            "latency_ms_p95",
        ]:
            if key not in item:
                failures.append(f"row_missing:{item.get('mode')}:{item.get('route')}:{key}")
        if int(item.get("fill_count", 0) or 0) <= 0:
            failures.append(f"fill_count_invalid:{item.get('mode')}:{item.get('route')}")
        if float(item.get("latency_ms_p50", -1.0) or -1.0) < 0.0:
            failures.append(f"latency_p50_invalid:{item.get('mode')}:{item.get('route')}")
        if float(item.get("latency_ms_p95", -1.0) or -1.0) < float(item.get("latency_ms_p50", -1.0) or -1.0):
            failures.append(f"latency_order_invalid:{item.get('mode')}:{item.get('route')}")

    paper_maker = next((item for item in items if item.get("mode") == "paper" and item.get("route") == "maker_bias"), {})
    paper_taker = next((item for item in items if item.get("mode") == "paper" and item.get("route") == "taker_primary"), {})
    shadow_maker = next((item for item in items if item.get("mode") == "shadow" and item.get("route") == "maker_bias"), {})

    if paper_maker.get("run_id") != "run-paper-06" or paper_taker.get("run_id") != "run-paper-06":
        failures.append("paper_rows_not_bound_to_latest_paper_run")
    if shadow_maker.get("run_id") != "run-shadow-06":
        failures.append("shadow_row_not_bound_to_latest_shadow_run")
    if float(paper_maker.get("avg_latency_ms", 0.0) or 0.0) >= float(paper_taker.get("avg_latency_ms", 0.0) or 0.0):
        failures.append("paper_route_latency_not_distinct")
    if float(shadow_maker.get("avg_latency_ms", 0.0) or 0.0) <= float(paper_maker.get("avg_latency_ms", 0.0) or 0.0):
        failures.append("mode_latency_not_distinct")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
