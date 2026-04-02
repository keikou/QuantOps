from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Execution_reality_next_lane_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_execution_reality_plan_doc")
    else:
        plan_text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "Execution Reality",
            "execution quality summary surface is explicit and internally coherent",
            "verify_execution_reality_next_lane.py",
        ]:
            if needle not in plan_text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.app.container import CONTAINER
    from ai_hedge_bot.app.main import app
    from ai_hedge_bot.api.routes import execution as execution_routes

    client = TestClient(app)

    execution_routes._execution_quality_summary_cache["expires_at"] = None
    execution_routes._execution_quality_summary_cache["payload"] = None
    original = dict(CONTAINER.latest_execution_quality)

    try:
        CONTAINER.latest_execution_quality = {
            "status": "ok",
            "snapshot_id": "snap-exec-1",
            "created_at": "2026-04-02T00:00:00+00:00",
            "run_id": "run-exec-1",
            "cycle_id": "cycle-exec-1",
            "mode": "paper",
            "order_count": 5,
            "fill_count": 4,
            "fill_rate": 0.8,
            "avg_slippage_bps": 1.2,
            "latency_ms_p50": 35.0,
            "latency_ms_p95": 80.0,
            "latest_fills": [{"fill_id": "ignored"}],
            "latest_plans": [{"plan_id": "ignored"}],
        }
        response = client.get("/execution/quality/latest_summary")
        if response.status_code != 200:
            failures.append(f"unexpected_status:{response.status_code}")
        else:
            payload = response.json()
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
            ]:
                if key not in payload:
                    failures.append(f"missing_field:{key}")

            if payload.get("fill_count", 0) > payload.get("order_count", 0):
                failures.append("fill_count_exceeds_order_count")

            fill_rate = payload.get("fill_rate")
            if fill_rate is None or not (0.0 <= float(fill_rate) <= 1.0):
                failures.append("fill_rate_out_of_range")

            p50 = payload.get("latency_ms_p50")
            p95 = payload.get("latency_ms_p95")
            if p50 is None or float(p50) < 0.0:
                failures.append("latency_p50_invalid")
            if p95 is None or float(p95) < 0.0:
                failures.append("latency_p95_invalid")
            if p50 is not None and p95 is not None and float(p95) < float(p50):
                failures.append("latency_percentiles_inverted")

            if "latest_fills" in payload:
                failures.append("latest_fills_not_trimmed")
            if "latest_plans" in payload:
                failures.append("latest_plans_not_trimmed")
    finally:
        CONTAINER.latest_execution_quality = original

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
