from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Execution_reality_packet04_mode_path_consistency_plan.md"
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
        failures.append("missing_packet04_plan_doc")
    else:
        plan_text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "run-scoped and mode-consistent",
            "/execution/quality/latest_summary",
            "/execution/quality/latest",
            "older record from another mode does not bleed",
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
                "snapshot_id": "snap-old-shadow",
                "created_at": now.isoformat(),
                "run_id": "run-old-shadow",
                "cycle_id": "cycle-old-shadow",
                "mode": "shadow",
                "order_count": 3,
                "fill_count": 3,
                "fill_rate": 1.0,
                "avg_slippage_bps": 0.5,
                "latency_ms_p50": 20.0,
                "latency_ms_p95": 25.0,
            },
            {
                "snapshot_id": "snap-new-paper",
                "created_at": (now + timedelta(seconds=5)).isoformat(),
                "run_id": "run-new-paper",
                "cycle_id": "cycle-new-paper",
                "mode": "paper",
                "order_count": 2,
                "fill_count": 1,
                "fill_rate": 0.5,
                "avg_slippage_bps": 2.2,
                "latency_ms_p50": 35.0,
                "latency_ms_p95": 55.0,
            },
        ],
    )

    CONTAINER.runtime_store.append(
        "execution_plans",
        [
            {
                "plan_id": "plan-old-shadow",
                "created_at": now.isoformat(),
                "run_id": "run-old-shadow",
                "mode": "shadow",
                "symbol": "BTCUSDT",
                "side": "buy",
                "target_weight": 0.1,
                "order_qty": 1.0,
                "limit_price": 100.0,
                "participation_rate": 0.1,
                "status": "planned",
                "algo": "twap",
                "route": "shadow_route",
                "expire_seconds": 120,
                "slice_count": 1,
                "metadata_json": "{}",
            },
            {
                "plan_id": "plan-new-paper",
                "created_at": (now + timedelta(seconds=5)).isoformat(),
                "run_id": "run-new-paper",
                "mode": "paper",
                "symbol": "ETHUSDT",
                "side": "sell",
                "target_weight": 0.05,
                "order_qty": 2.0,
                "limit_price": 200.0,
                "participation_rate": 0.1,
                "status": "planned",
                "algo": "twap",
                "route": "paper_route",
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
                "fill_id": "fill-old-shadow",
                "created_at": (now + timedelta(seconds=1)).isoformat(),
                "run_id": "run-old-shadow",
                "mode": "shadow",
                "plan_id": "plan-old-shadow",
                "order_id": "order-old-shadow",
                "client_order_id": "client-old-shadow",
                "strategy_id": "strategy-shadow",
                "alpha_family": "trend",
                "symbol": "BTCUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 100.1,
                "slippage_bps": 0.5,
                "latency_ms": 20.0,
                "fee_bps": 0.1,
                "bid": 100.0,
                "ask": 100.2,
                "arrival_mid_price": 100.1,
                "price_source": "shadow_quote",
                "quote_time": (now + timedelta(seconds=1)).isoformat(),
                "quote_age_sec": 0.1,
                "fallback_reason": None,
                "status": "filled",
            },
            {
                "fill_id": "fill-new-paper",
                "created_at": (now + timedelta(seconds=6)).isoformat(),
                "run_id": "run-new-paper",
                "mode": "paper",
                "plan_id": "plan-new-paper",
                "order_id": "order-new-paper",
                "client_order_id": "client-new-paper",
                "strategy_id": "strategy-paper",
                "alpha_family": "mean_reversion",
                "symbol": "ETHUSDT",
                "side": "sell",
                "fill_qty": 1.0,
                "fill_price": 199.8,
                "slippage_bps": 2.2,
                "latency_ms": 35.0,
                "fee_bps": 0.1,
                "bid": 199.7,
                "ask": 199.9,
                "arrival_mid_price": 199.8,
                "price_source": "paper_quote",
                "quote_time": (now + timedelta(seconds=6)).isoformat(),
                "quote_age_sec": 0.1,
                "fallback_reason": None,
                "status": "filled",
            },
        ],
    )

    from ai_hedge_bot.app.container import CONTAINER as CONTAINER_REF
    CONTAINER_REF.latest_execution_quality = {}

    summary = client.get("/execution/quality/latest_summary").json()
    detail = client.get("/execution/quality/latest").json()

    expected_run = "run-new-paper"
    expected_cycle = "cycle-new-paper"
    expected_mode = "paper"

    for payload_name, payload in [("summary", summary), ("detail", detail)]:
        if payload.get("run_id") != expected_run:
            failures.append(f"{payload_name}_run_id_mismatch")
        if payload.get("cycle_id") != expected_cycle:
            failures.append(f"{payload_name}_cycle_id_mismatch")
        if payload.get("mode") != expected_mode:
            failures.append(f"{payload_name}_mode_mismatch")

    latest_fills = detail.get("latest_fills", [])
    if not latest_fills:
        failures.append("detail_missing_latest_fills")
    else:
        if any(row.get("run_id") != expected_run for row in latest_fills):
            failures.append("detail_latest_fills_cross_run_bleed")
        if any(row.get("mode") != expected_mode for row in latest_fills):
            failures.append("detail_latest_fills_cross_mode_bleed")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
