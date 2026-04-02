from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Governance_runtime_control_packet03_latency_throttle_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-grtc-c3-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def _reset_runtime_state(container, execution_routes) -> None:
    execution_routes._execution_quality_summary_cache["expires_at"] = None
    execution_routes._execution_quality_summary_cache["payload"] = None
    for table in [
        "execution_quality_snapshots",
        "execution_plans",
        "execution_fills",
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
            "/governance/runtime-control/latency-throttle/latest",
            "allow / throttle / stop",
            "participation_rate_multiplier",
            "slice_interval_multiplier",
        ]:
            if needle not in plan_text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.app.container import CONTAINER
    from ai_hedge_bot.api.routes import execution as execution_routes
    from ai_hedge_bot.services.governance_runtime_control_service import GovernanceRuntimeControlService

    _reset_runtime_state(CONTAINER, execution_routes)

    now = datetime.now(timezone.utc)
    run_id = "run-grtc-c3"
    cycle_id = "cycle-grtc-c3"
    CONTAINER.runtime_store.append(
        "execution_quality_snapshots",
        {
            "snapshot_id": "snap-grtc-c3",
            "created_at": (now + timedelta(seconds=6)).isoformat(),
            "run_id": run_id,
            "cycle_id": cycle_id,
            "mode": "shadow",
            "order_count": 3,
            "fill_count": 3,
            "fill_rate": 1.0,
            "avg_slippage_bps": 2.0,
            "latency_ms_p50": 28.0,
            "latency_ms_p95": 65.0,
        },
    )
    CONTAINER.runtime_store.append(
        "execution_plans",
        [
            {
                "plan_id": "plan-c3-fast",
                "created_at": (now + timedelta(seconds=4)).isoformat(),
                "run_id": run_id,
                "mode": "shadow",
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
                "plan_id": "plan-c3-mid",
                "created_at": (now + timedelta(seconds=5)).isoformat(),
                "run_id": run_id,
                "mode": "shadow",
                "symbol": "ETHUSDT",
                "side": "buy",
                "target_weight": 0.1,
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
                "plan_id": "plan-c3-slow",
                "created_at": (now + timedelta(seconds=6)).isoformat(),
                "run_id": run_id,
                "mode": "shadow",
                "symbol": "SOLUSDT",
                "side": "buy",
                "target_weight": 0.1,
                "order_qty": 1.0,
                "limit_price": 50.0,
                "participation_rate": 0.2,
                "status": "planned",
                "algo": "twap",
                "route": "slow_path",
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
                "fill_id": "fill-c3-fast",
                "created_at": (now + timedelta(seconds=4)).isoformat(),
                "run_id": run_id,
                "mode": "shadow",
                "plan_id": "plan-c3-fast",
                "order_id": "order-c3-fast",
                "client_order_id": "client-c3-fast",
                "strategy_id": "strategy-c3",
                "alpha_family": "trend",
                "symbol": "BTCUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 100.0,
                "slippage_bps": 1.0,
                "latency_ms": 18.0,
                "fee_bps": 0.1,
                "bid": 99.9,
                "ask": 100.1,
                "arrival_mid_price": 100.0,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=4)).isoformat(),
                "quote_age_sec": 0.1,
                "fallback_reason": None,
                "status": "filled",
            },
            {
                "fill_id": "fill-c3-mid",
                "created_at": (now + timedelta(seconds=5)).isoformat(),
                "run_id": run_id,
                "mode": "shadow",
                "plan_id": "plan-c3-mid",
                "order_id": "order-c3-mid",
                "client_order_id": "client-c3-mid",
                "strategy_id": "strategy-c3",
                "alpha_family": "trend",
                "symbol": "ETHUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 200.0,
                "slippage_bps": 2.0,
                "latency_ms": 42.0,
                "fee_bps": 0.1,
                "bid": 199.9,
                "ask": 200.1,
                "arrival_mid_price": 200.0,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=5)).isoformat(),
                "quote_age_sec": 0.1,
                "fallback_reason": None,
                "status": "filled",
            },
            {
                "fill_id": "fill-c3-slow",
                "created_at": (now + timedelta(seconds=6)).isoformat(),
                "run_id": run_id,
                "mode": "shadow",
                "plan_id": "plan-c3-slow",
                "order_id": "order-c3-slow",
                "client_order_id": "client-c3-slow",
                "strategy_id": "strategy-c3",
                "alpha_family": "trend",
                "symbol": "SOLUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 50.0,
                "slippage_bps": 2.0,
                "latency_ms": 95.0,
                "fee_bps": 0.1,
                "bid": 49.9,
                "ask": 50.1,
                "arrival_mid_price": 50.0,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=6)).isoformat(),
                "quote_age_sec": 0.1,
                "fallback_reason": None,
                "status": "filled",
            },
        ],
    )

    payload = GovernanceRuntimeControlService().latency_throttle_latest()
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")
    if payload.get("run_id") != run_id:
        failures.append("run_id_mismatch")
    if payload.get("cycle_id") != cycle_id:
        failures.append("cycle_id_mismatch")
    if payload.get("mode") != "shadow":
        failures.append("mode_mismatch")

    items = payload.get("items", [])
    if len(items) != 3:
        failures.append("route_decision_count_mismatch")

    by_route = {str(item.get("route") or ""): item for item in items}
    fast = by_route.get("maker_bias")
    mid = by_route.get("taker_primary")
    slow = by_route.get("slow_path")
    if fast is None:
        failures.append("fast_route_missing")
    if mid is None:
        failures.append("mid_route_missing")
    if slow is None:
        failures.append("slow_route_missing")

    for item in items:
        for key in [
            "route",
            "avg_latency_ms",
            "latency_ms_p50",
            "latency_ms_p95",
            "decision",
            "reason",
            "participation_rate_multiplier",
            "slice_interval_multiplier",
        ]:
            if key not in item:
                failures.append(f"row_missing:{item.get('route')}:{key}")

    if fast and fast.get("decision") != "allow":
        failures.append("fast_route_should_allow")
    if mid and mid.get("decision") != "throttle":
        failures.append("mid_route_should_throttle")
    if slow and slow.get("decision") != "stop":
        failures.append("slow_route_should_stop")
    if fast and float(fast.get("participation_rate_multiplier", -1.0)) != 1.0:
        failures.append("fast_participation_invalid")
    if mid and float(mid.get("participation_rate_multiplier", -1.0)) != 0.5:
        failures.append("mid_participation_invalid")
    if slow and float(slow.get("participation_rate_multiplier", -1.0)) != 0.0:
        failures.append("slow_participation_invalid")

    summary = payload.get("decision_summary") or {}
    if int(summary.get("allowed_routes", -1) or -1) != 1:
        failures.append("allowed_route_count_invalid")
    if int(summary.get("throttled_routes", -1) or -1) != 1:
        failures.append("throttled_route_count_invalid")
    if int(summary.get("stopped_routes", -1) or -1) != 1:
        failures.append("stopped_route_count_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
