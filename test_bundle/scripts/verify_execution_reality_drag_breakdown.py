from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Execution_reality_packet08_drag_breakdown_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def _reset_runtime_state(container, execution_routes) -> None:
    execution_routes._execution_quality_summary_cache["expires_at"] = None
    execution_routes._execution_quality_summary_cache["payload"] = None
    for table in [
        "execution_quality_snapshots",
        "shadow_pnl_snapshots",
    ]:
        try:
            container.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_packet08_plan_doc")
    else:
        plan_text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/execution/quality/drag-breakdown/latest",
            "execution drag decomposition is explicit for the latest run",
            "component_sum_usd = slippage_drag_usd + fee_drag_usd + latency_drag_usd",
            "execution_drag_usd = gross_alpha_pnl_usd - net_shadow_pnl_usd",
        ]:
            if needle not in plan_text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.app.container import CONTAINER
    from ai_hedge_bot.app.main import app
    from ai_hedge_bot.api.routes import execution as execution_routes

    client = TestClient(app)
    _reset_runtime_state(CONTAINER, execution_routes)

    now = datetime.now(timezone.utc)
    run_id = "run-drag-08"
    CONTAINER.runtime_store.append(
        "execution_quality_snapshots",
        {
            "snapshot_id": "snap-drag-08",
            "created_at": (now + timedelta(seconds=2)).isoformat(),
            "run_id": run_id,
            "cycle_id": "cycle-drag-08",
            "mode": "shadow",
            "order_count": 4,
            "fill_count": 4,
            "fill_rate": 1.0,
            "avg_slippage_bps": 3.2,
            "latency_ms_p50": 24.0,
            "latency_ms_p95": 42.0,
        },
    )
    CONTAINER.runtime_store.append(
        "shadow_pnl_snapshots",
        {
            "run_id": run_id,
            "created_at": (now + timedelta(seconds=3)).isoformat(),
            "gross_alpha_pnl_usd": 120.0,
            "net_shadow_pnl_usd": 108.0,
            "execution_drag_usd": 12.0,
            "slippage_drag_usd": 5.0,
            "fee_drag_usd": 4.0,
            "latency_drag_usd": 3.0,
        },
    )

    payload = client.get("/execution/quality/drag-breakdown/latest").json()

    for key in ["run_id", "mode", "drag", "linkage"]:
        if key not in payload:
            failures.append(f"payload_missing:{key}")

    if payload.get("run_id") != run_id:
        failures.append("run_id_mismatch")
    if payload.get("mode") != "shadow":
        failures.append("mode_mismatch")

    drag = payload.get("drag") or {}
    linkage = payload.get("linkage") or {}
    for key in [
        "gross_alpha_pnl_usd",
        "net_shadow_pnl_usd",
        "execution_drag_usd",
        "slippage_drag_usd",
        "fee_drag_usd",
        "latency_drag_usd",
        "component_sum_usd",
    ]:
        if key not in drag:
            failures.append(f"drag_missing:{key}")

    for key in ["quality_run_id", "drag_run_id", "run_id_match"]:
        if key not in linkage:
            failures.append(f"linkage_missing:{key}")

    if linkage.get("quality_run_id") != run_id or linkage.get("drag_run_id") != run_id:
        failures.append("linkage_run_id_mismatch")
    if not linkage.get("run_id_match"):
        failures.append("run_id_match_false")

    gross = float(drag.get("gross_alpha_pnl_usd", 0.0) or 0.0)
    net = float(drag.get("net_shadow_pnl_usd", 0.0) or 0.0)
    execution_drag = float(drag.get("execution_drag_usd", 0.0) or 0.0)
    slippage_drag = float(drag.get("slippage_drag_usd", 0.0) or 0.0)
    fee_drag = float(drag.get("fee_drag_usd", 0.0) or 0.0)
    latency_drag = float(drag.get("latency_drag_usd", 0.0) or 0.0)
    component_sum = float(drag.get("component_sum_usd", 0.0) or 0.0)

    if abs(component_sum - (slippage_drag + fee_drag + latency_drag)) > 1e-9:
        failures.append("component_sum_invalid")
    if abs(execution_drag - (gross - net)) > 1e-9:
        failures.append("execution_drag_arithmetic_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
