from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Execution_reality_packet07_pnl_linkage_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def _reset_runtime_state(container, execution_routes, portfolio_routes) -> None:
    execution_routes._execution_quality_summary_cache["expires_at"] = None
    execution_routes._execution_quality_summary_cache["payload"] = None
    portfolio_routes._portfolio_overview_summary_cache["expires_at"] = None
    portfolio_routes._portfolio_overview_summary_cache["payload"] = None
    for table in [
        "execution_fills",
        "execution_quality_snapshots",
        "equity_snapshots",
        "position_snapshots_latest",
    ]:
        try:
            container.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_packet07_plan_doc")
    else:
        plan_text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/execution/quality/pnl-linkage/latest",
            "run_id matches the portfolio snapshot run_id",
            "gross_pnl = realized_pnl + unrealized_pnl",
            "net_pnl_after_fees = gross_pnl - fees_paid",
        ]:
            if needle not in plan_text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.app.container import CONTAINER
    from ai_hedge_bot.app.main import app
    from ai_hedge_bot.api.routes import execution as execution_routes
    from ai_hedge_bot.api.routes import portfolio as portfolio_routes

    client = TestClient(app)
    _reset_runtime_state(CONTAINER, execution_routes, portfolio_routes)

    now = datetime.now(timezone.utc)
    run_id = "run-pnl-link-07"
    cycle_id = "cycle-pnl-link-07"
    snapshot_time = (now + timedelta(seconds=4)).isoformat()

    CONTAINER.runtime_store.append(
        "execution_quality_snapshots",
        {
            "snapshot_id": "snap-pnl-link-07",
            "created_at": (now + timedelta(seconds=3)).isoformat(),
            "run_id": run_id,
            "cycle_id": cycle_id,
            "mode": "paper",
            "order_count": 3,
            "fill_count": 2,
            "fill_rate": 2.0 / 3.0,
            "avg_slippage_bps": 2.6,
            "latency_ms_p50": 25.0,
            "latency_ms_p95": 40.0,
        },
    )

    CONTAINER.runtime_store.append(
        "execution_fills",
        {
            "fill_id": "fill-pnl-link-07",
            "created_at": (now + timedelta(seconds=3)).isoformat(),
            "run_id": run_id,
            "mode": "paper",
            "plan_id": "plan-pnl-link-07",
            "order_id": "order-pnl-link-07",
            "client_order_id": "client-pnl-link-07",
            "strategy_id": "strategy-pnl-link-07",
            "alpha_family": "trend",
            "symbol": "BTCUSDT",
            "side": "buy",
            "fill_qty": 1.0,
            "fill_price": 100.2,
            "slippage_bps": 2.6,
            "latency_ms": 25.0,
            "fee_bps": 0.1,
            "bid": 100.1,
            "ask": 100.3,
            "arrival_mid_price": 100.2,
            "price_source": "quote_test",
            "quote_time": (now + timedelta(seconds=3)).isoformat(),
            "quote_age_sec": 0.1,
            "fallback_reason": None,
            "status": "filled",
        },
    )

    CONTAINER.runtime_store.append(
        "equity_snapshots",
        {
            "snapshot_time": snapshot_time,
            "cash_balance": 900.0,
            "free_cash": 900.0,
            "used_margin": 100.0,
            "collateral_equity": 1000.0,
            "available_margin": 900.0,
            "margin_utilization": 0.1,
            "gross_exposure": 250.0,
            "net_exposure": 250.0,
            "long_exposure": 250.0,
            "short_exposure": 0.0,
            "market_value": 250.0,
            "unrealized_pnl": 7.5,
            "realized_pnl": 12.5,
            "fees_paid": 1.5,
            "total_equity": 1018.5,
            "drawdown": 0.02,
            "peak_equity": 1025.0,
        },
    )

    CONTAINER.runtime_store.append(
        "position_snapshots_latest",
        {
            "symbol": "BTCUSDT",
            "strategy_id": "strategy-pnl-link-07",
            "alpha_family": "trend",
            "signed_qty": 1.0,
            "abs_qty": 1.0,
            "side": "long",
            "avg_entry_price": 100.0,
            "mark_price": 107.5,
            "market_value": 107.5,
            "unrealized_pnl": 7.5,
            "realized_pnl": 12.5,
            "exposure_notional": 107.5,
            "price_source": "quote_test",
            "quote_time": snapshot_time,
            "quote_age_sec": 0.1,
            "stale": False,
            "updated_at": snapshot_time,
        },
    )

    payload = client.get("/execution/quality/pnl-linkage/latest").json()

    for key in ["run_id", "cycle_id", "mode", "execution_quality", "portfolio_pnl", "linkage"]:
        if key not in payload:
            failures.append(f"payload_missing:{key}")

    if payload.get("run_id") != run_id:
        failures.append("run_id_mismatch")
    if payload.get("cycle_id") != cycle_id:
        failures.append("cycle_id_mismatch")
    if payload.get("mode") != "paper":
        failures.append("mode_mismatch")

    execution_quality = payload.get("execution_quality") or {}
    portfolio_pnl = payload.get("portfolio_pnl") or {}
    linkage = payload.get("linkage") or {}

    for key in ["order_count", "fill_count", "fill_rate", "avg_slippage_bps", "latency_ms_p50", "latency_ms_p95"]:
        if key not in execution_quality:
            failures.append(f"execution_quality_missing:{key}")

    for key in ["portfolio_run_id", "total_equity", "realized_pnl", "unrealized_pnl", "gross_pnl", "fees_paid", "net_pnl_after_fees", "drawdown"]:
        if key not in portfolio_pnl:
            failures.append(f"portfolio_pnl_missing:{key}")

    if portfolio_pnl.get("portfolio_run_id") != run_id:
        failures.append("portfolio_run_id_mismatch")
    if not linkage.get("run_id_match"):
        failures.append("run_id_linkage_missing")

    realized = float(portfolio_pnl.get("realized_pnl", 0.0) or 0.0)
    unrealized = float(portfolio_pnl.get("unrealized_pnl", 0.0) or 0.0)
    gross = float(portfolio_pnl.get("gross_pnl", 0.0) or 0.0)
    fees = float(portfolio_pnl.get("fees_paid", 0.0) or 0.0)
    net = float(portfolio_pnl.get("net_pnl_after_fees", 0.0) or 0.0)

    if abs(gross - (realized + unrealized)) > 1e-9:
        failures.append("gross_pnl_arithmetic_invalid")
    if abs(net - (gross - fees)) > 1e-9:
        failures.append("net_pnl_arithmetic_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
