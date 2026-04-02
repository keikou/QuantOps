from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "Execution_reality_baseline_metrics_v1.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def _reset_runtime_state(container, execution_routes) -> None:
    execution_routes._execution_quality_summary_cache["expires_at"] = None
    execution_routes._execution_quality_summary_cache["payload"] = None
    for table in [
        "execution_quality_snapshots",
        "execution_plans",
        "execution_fills",
        "shadow_pnl_snapshots",
    ]:
        try:
            container.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def main() -> None:
    failures: list[str] = []

    if not DOC.exists():
        failures.append("missing_execution_reality_baseline_doc")
    else:
        text = DOC.read_text(encoding="utf-8")
        for needle in [
            "/execution/quality/by-mode",
            "/execution/quality/route-leakage/latest",
            "/execution/quality/latency-by-mode-route",
            "/execution/quality/drag-breakdown/latest",
            "/execution/quality/symbol-leakage/latest",
            "execution_drag_pct = execution_drag_usd / gross_alpha_pnl_usd",
        ]:
            if needle not in text:
                failures.append(f"doc_missing:{needle}")

    from ai_hedge_bot.app.container import CONTAINER
    from ai_hedge_bot.app.main import app
    from ai_hedge_bot.api.routes import execution as execution_routes

    client = TestClient(app)
    _reset_runtime_state(CONTAINER, execution_routes)

    now = datetime.now(timezone.utc)
    run_shadow = "run-baseline-shadow"
    run_paper = "run-baseline-paper"

    CONTAINER.runtime_store.append(
        "execution_quality_snapshots",
        [
            {
                "snapshot_id": "snap-baseline-paper",
                "created_at": (now + timedelta(seconds=2)).isoformat(),
                "run_id": run_paper,
                "cycle_id": "cycle-baseline-paper",
                "mode": "paper",
                "order_count": 2,
                "fill_count": 2,
                "fill_rate": 1.0,
                "avg_slippage_bps": 1.5,
                "latency_ms_p50": 15.0,
                "latency_ms_p95": 25.0,
            },
            {
                "snapshot_id": "snap-baseline-shadow",
                "created_at": (now + timedelta(seconds=4)).isoformat(),
                "run_id": run_shadow,
                "cycle_id": "cycle-baseline-shadow",
                "mode": "shadow",
                "order_count": 3,
                "fill_count": 3,
                "fill_rate": 1.0,
                "avg_slippage_bps": 3.5,
                "latency_ms_p50": 22.0,
                "latency_ms_p95": 45.0,
            },
        ],
    )

    CONTAINER.runtime_store.append(
        "execution_plans",
        [
            {
                "plan_id": "plan-paper-maker",
                "created_at": (now + timedelta(seconds=2)).isoformat(),
                "run_id": run_paper,
                "mode": "paper",
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
                "plan_id": "plan-shadow-maker",
                "created_at": (now + timedelta(seconds=4)).isoformat(),
                "run_id": run_shadow,
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
                "plan_id": "plan-shadow-taker",
                "created_at": (now + timedelta(seconds=4)).isoformat(),
                "run_id": run_shadow,
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
                "fill_id": "fill-paper-maker",
                "created_at": (now + timedelta(seconds=2)).isoformat(),
                "run_id": run_paper,
                "mode": "paper",
                "plan_id": "plan-paper-maker",
                "order_id": "order-paper-maker",
                "client_order_id": "client-paper-maker",
                "strategy_id": "strategy-paper",
                "alpha_family": "trend",
                "symbol": "BTCUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 200.0,
                "slippage_bps": 1.5,
                "latency_ms": 15.0,
                "fee_bps": 1.0,
                "bid": 199.9,
                "ask": 200.1,
                "arrival_mid_price": 200.0,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=2)).isoformat(),
                "quote_age_sec": 0.1,
                "fallback_reason": None,
                "status": "filled",
            },
            {
                "fill_id": "fill-shadow-maker",
                "created_at": (now + timedelta(seconds=4)).isoformat(),
                "run_id": run_shadow,
                "mode": "shadow",
                "plan_id": "plan-shadow-maker",
                "order_id": "order-shadow-maker",
                "client_order_id": "client-shadow-maker",
                "strategy_id": "strategy-shadow",
                "alpha_family": "trend",
                "symbol": "BTCUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 200.0,
                "slippage_bps": 2.5,
                "latency_ms": 20.0,
                "fee_bps": 1.0,
                "bid": 199.9,
                "ask": 200.1,
                "arrival_mid_price": 200.0,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=4)).isoformat(),
                "quote_age_sec": 0.1,
                "fallback_reason": None,
                "status": "filled",
            },
            {
                "fill_id": "fill-shadow-taker",
                "created_at": (now + timedelta(seconds=5)).isoformat(),
                "run_id": run_shadow,
                "mode": "shadow",
                "plan_id": "plan-shadow-taker",
                "order_id": "order-shadow-taker",
                "client_order_id": "client-shadow-taker",
                "strategy_id": "strategy-shadow",
                "alpha_family": "trend",
                "symbol": "ETHUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 300.0,
                "slippage_bps": 4.5,
                "latency_ms": 45.0,
                "fee_bps": 2.0,
                "bid": 299.9,
                "ask": 300.1,
                "arrival_mid_price": 300.0,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=5)).isoformat(),
                "quote_age_sec": 0.1,
                "fallback_reason": None,
                "status": "filled",
            },
        ],
    )

    CONTAINER.runtime_store.append(
        "shadow_pnl_snapshots",
        {
            "snapshot_id": "spnl-baseline-shadow",
            "created_at": (now + timedelta(seconds=6)).isoformat(),
            "run_id": run_shadow,
            "cycle_id": "cycle-baseline-shadow",
            "order_count": 3,
            "fill_count": 3,
            "gross_alpha_pnl_usd": 100.0,
            "net_shadow_pnl_usd": 88.0,
            "execution_drag_usd": 12.0,
            "slippage_drag_usd": 5.0,
            "fee_drag_usd": 4.0,
            "latency_drag_usd": 3.0,
        },
    )

    by_mode = client.get("/execution/quality/by-mode").json()
    route_leakage = client.get("/execution/quality/route-leakage/latest").json()
    latency = client.get("/execution/quality/latency-by-mode-route").json()
    drag = client.get("/execution/quality/drag-breakdown/latest").json()
    symbol_leakage = client.get("/execution/quality/symbol-leakage/latest").json()

    mode_rows = by_mode.get("items", [])
    if len(mode_rows) < 2:
        failures.append("baseline_missing_mode_rows")
    else:
        modes = {row.get("mode") for row in mode_rows}
        if not {"paper", "shadow"}.issubset(modes):
            failures.append("baseline_modes_incomplete")

    route_rows = route_leakage.get("items", [])
    if len(route_rows) < 2:
        failures.append("baseline_missing_route_rows")

    latency_rows = latency.get("items", [])
    if not latency_rows:
        failures.append("baseline_missing_latency_rows")
    elif any(float(row.get("latency_ms_p95", -1.0) or -1.0) < float(row.get("latency_ms_p50", -1.0) or -1.0) for row in latency_rows):
        failures.append("baseline_latency_incoherent")

    drag_row = drag.get("drag") or {}
    gross_alpha = float(drag_row.get("gross_alpha_pnl_usd", 0.0) or 0.0)
    execution_drag = float(drag_row.get("execution_drag_usd", 0.0) or 0.0)
    if gross_alpha <= 0.0:
        failures.append("baseline_gross_alpha_nonpositive")
    else:
        execution_drag_pct = execution_drag / gross_alpha
        if execution_drag_pct < 0.0:
            failures.append("baseline_execution_drag_pct_negative")

    symbol_rows = symbol_leakage.get("items", [])
    if len(symbol_rows) < 2:
        failures.append("baseline_missing_symbol_rows")
    else:
        sorted_symbols = sorted(symbol_rows, key=lambda row: float(row.get("execution_drag_usd", 0.0) or 0.0), reverse=True)
        if sorted_symbols[0].get("symbol") != "ETHUSDT":
            failures.append("baseline_top_leakage_symbol_unexpected")
        symbol_drag_sum = sum(float(row.get("execution_drag_usd", 0.0) or 0.0) for row in symbol_rows)
        if abs(symbol_drag_sum - execution_drag) > 1e-9:
            failures.append("baseline_symbol_drag_total_mismatch")

    if route_rows:
        sorted_routes = sorted(route_rows, key=lambda row: float(row.get("execution_drag_usd", 0.0) or 0.0), reverse=True)
        if sorted_routes[0].get("route") != "taker_primary":
            failures.append("baseline_top_leakage_route_unexpected")
        route_drag_sum = sum(float(row.get("execution_drag_usd", 0.0) or 0.0) for row in route_rows)
        if abs(route_drag_sum - execution_drag) > 1e-9:
            failures.append("baseline_route_drag_total_mismatch")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
