from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Execution_reality_packet03_slippage_visibility_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def _reset_runtime_state(container, execution_routes) -> None:
    execution_routes._execution_quality_summary_cache["expires_at"] = None
    execution_routes._execution_quality_summary_cache["payload"] = None
    for table in [
        "execution_fills",
        "execution_quality_snapshots",
    ]:
        try:
            container.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_packet03_plan_doc")
    else:
        plan_text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "slippage evidence is visible on both summary and fill surfaces",
            "/execution/quality/latest_summary",
            "/execution/fills",
            "quote-attributable",
        ]:
            if needle not in plan_text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.app.container import CONTAINER
    from ai_hedge_bot.app.main import app
    from ai_hedge_bot.api.routes import execution as execution_routes

    client = TestClient(app)
    _reset_runtime_state(CONTAINER, execution_routes)

    now = datetime.now(timezone.utc)
    run_id = "run-exec-slip-1"
    cycle_id = "cycle-exec-slip-1"
    fill_time = (now + timedelta(seconds=1)).isoformat()

    CONTAINER.latest_execution_quality = {
        "status": "ok",
        "snapshot_id": "snap-slip-1",
        "created_at": now.isoformat(),
        "run_id": run_id,
        "cycle_id": cycle_id,
        "mode": "paper",
        "order_count": 1,
        "fill_count": 1,
        "fill_rate": 1.0,
        "avg_slippage_bps": 2.5,
        "latency_ms_p50": 30.0,
        "latency_ms_p95": 45.0,
    }

    CONTAINER.runtime_store.append(
        "execution_fills",
        {
            "fill_id": "fill-slip-1",
            "created_at": fill_time,
            "run_id": run_id,
            "mode": "paper",
            "plan_id": "plan-slip-1",
            "order_id": "order-slip-1",
            "client_order_id": "client-slip-1",
            "strategy_id": "strategy-slip-1",
            "alpha_family": "trend",
            "symbol": "BTCUSDT",
            "side": "buy",
            "fill_qty": 1.0,
            "fill_price": 100.25,
            "slippage_bps": 2.5,
            "latency_ms": 30.0,
            "fee_bps": 0.1,
            "bid": 100.20,
            "ask": 100.30,
            "arrival_mid_price": 100.225,
            "price_source": "quote_test",
            "quote_time": fill_time,
            "quote_age_sec": 0.05,
            "fallback_reason": None,
            "status": "filled",
        },
    )

    summary = client.get("/execution/quality/latest_summary").json()
    fills = client.get("/execution/fills").json()

    for key in ["run_id", "cycle_id", "mode", "avg_slippage_bps"]:
        if key not in summary:
            failures.append(f"summary_missing:{key}")

    if summary.get("run_id") != run_id:
        failures.append("summary_run_id_mismatch")
    if summary.get("cycle_id") != cycle_id:
        failures.append("summary_cycle_id_mismatch")
    if float(summary.get("avg_slippage_bps", -1.0)) < 0.0:
        failures.append("summary_slippage_invalid")

    items = fills.get("items", [])
    fill = next((row for row in items if row.get("fill_id") == "fill-slip-1"), None)
    if fill is None:
        failures.append("fill_row_missing")
    else:
        for key in [
            "slippage_bps",
            "bid",
            "ask",
            "arrival_mid_price",
            "price_source",
            "quote_time",
            "quote_age_sec",
        ]:
            if key not in fill:
                failures.append(f"fill_missing:{key}")
        if float(fill.get("slippage_bps", -1.0)) < 0.0:
            failures.append("fill_slippage_invalid")
        if not fill.get("price_source"):
            failures.append("fill_price_source_missing")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
