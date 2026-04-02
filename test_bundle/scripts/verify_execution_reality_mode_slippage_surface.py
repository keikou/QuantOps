from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Execution_reality_packet05_mode_slippage_surface_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def _reset_runtime_state(container, execution_routes) -> None:
    execution_routes._execution_quality_summary_cache["expires_at"] = None
    execution_routes._execution_quality_summary_cache["payload"] = None
    for table in [
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
        failures.append("missing_packet05_plan_doc")
    else:
        plan_text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/execution/quality/by-mode",
            "mode-separated",
            "route-attributable",
            "paper and shadow mode rows do not collapse",
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
                "snapshot_id": "snap-paper-05",
                "created_at": (now + timedelta(seconds=3)).isoformat(),
                "run_id": "run-paper-05",
                "cycle_id": "cycle-paper-05",
                "mode": "paper",
                "order_count": 4,
                "fill_count": 3,
                "fill_rate": 0.75,
                "avg_slippage_bps": 1.1,
                "latency_ms_p50": 18.0,
                "latency_ms_p95": 30.0,
            },
            {
                "snapshot_id": "snap-shadow-05",
                "created_at": (now + timedelta(seconds=6)).isoformat(),
                "run_id": "run-shadow-05",
                "cycle_id": "cycle-shadow-05",
                "mode": "shadow",
                "order_count": 5,
                "fill_count": 5,
                "fill_rate": 1.0,
                "avg_slippage_bps": 4.4,
                "latency_ms_p50": 24.0,
                "latency_ms_p95": 44.0,
            },
        ],
    )

    CONTAINER.runtime_store.append(
        "execution_plans",
        [
            {
                "plan_id": "plan-paper-05",
                "created_at": (now + timedelta(seconds=3)).isoformat(),
                "run_id": "run-paper-05",
                "mode": "paper",
                "symbol": "BTCUSDT",
                "side": "buy",
                "target_weight": 0.1,
                "order_qty": 1.0,
                "limit_price": 100.0,
                "participation_rate": 0.2,
                "status": "planned",
                "algo": "twap",
                "route": "paper_route",
                "expire_seconds": 120,
                "slice_count": 1,
                "metadata_json": "{}",
            },
            {
                "plan_id": "plan-shadow-05",
                "created_at": (now + timedelta(seconds=6)).isoformat(),
                "run_id": "run-shadow-05",
                "mode": "shadow",
                "symbol": "ETHUSDT",
                "side": "sell",
                "target_weight": 0.2,
                "order_qty": 2.0,
                "limit_price": 200.0,
                "participation_rate": 0.15,
                "status": "planned",
                "algo": "twap",
                "route": "shadow_route",
                "expire_seconds": 120,
                "slice_count": 1,
                "metadata_json": "{}",
            },
        ],
    )

    payload = client.get("/execution/quality/by-mode").json()

    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    items = payload.get("items", [])
    if len(items) < 2:
        failures.append("insufficient_mode_rows")

    by_mode = {str(item.get("mode") or ""): item for item in items}
    for expected_mode in ["paper", "shadow"]:
        item = by_mode.get(expected_mode)
        if item is None:
            failures.append(f"missing_mode:{expected_mode}")
            continue
        for key in [
            "run_id",
            "cycle_id",
            "mode",
            "order_count",
            "fill_count",
            "fill_rate",
            "avg_slippage_bps",
            "latency_ms_p50",
            "latency_ms_p95",
            "route_mix",
        ]:
            if key not in item:
                failures.append(f"{expected_mode}_missing:{key}")
        if not item.get("route_mix"):
            failures.append(f"{expected_mode}_route_mix_empty")

    paper = by_mode.get("paper", {})
    shadow = by_mode.get("shadow", {})
    if paper.get("run_id") == shadow.get("run_id"):
        failures.append("paper_shadow_run_collapsed")
    if float(paper.get("avg_slippage_bps", -1.0) or -1.0) >= float(shadow.get("avg_slippage_bps", -1.0) or -1.0):
        failures.append("mode_slippage_not_distinct")
    if "paper_route" not in (paper.get("route_mix") or {}):
        failures.append("paper_route_missing")
    if "shadow_route" not in (shadow.get("route_mix") or {}):
        failures.append("shadow_route_missing")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
