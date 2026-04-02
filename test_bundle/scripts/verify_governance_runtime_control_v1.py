from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Governance_runtime_control_v1_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-grtc-c1-", dir=str(REPO_ROOT / "runtime")))

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
        "shadow_pnl_snapshots",
    ]:
        try:
            container.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_governance_runtime_control_plan_doc")
    else:
        plan_text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "Governance -> Runtime Control",
            "/governance/runtime-control/routing/latest",
            "allow",
            "degrade",
            "block",
            "target_weight_multiplier",
        ]:
            if needle not in plan_text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.app.container import CONTAINER
    from ai_hedge_bot.api.routes import execution as execution_routes
    from ai_hedge_bot.services.governance_runtime_control_service import GovernanceRuntimeControlService

    _reset_runtime_state(CONTAINER, execution_routes)

    now = datetime.now(timezone.utc)
    run_id = "run-grtc-c1"
    CONTAINER.runtime_store.append(
        "execution_quality_snapshots",
        {
            "snapshot_id": "snap-grtc-c1",
            "created_at": (now + timedelta(seconds=2)).isoformat(),
            "run_id": run_id,
            "cycle_id": "cycle-grtc-c1",
            "mode": "shadow",
            "order_count": 2,
            "fill_count": 2,
            "fill_rate": 1.0,
            "avg_slippage_bps": 3.0,
            "latency_ms_p50": 20.0,
            "latency_ms_p95": 35.0,
        },
    )
    CONTAINER.runtime_store.append(
        "shadow_pnl_snapshots",
        {
            "snapshot_id": "spnl-grtc-c1",
            "created_at": (now + timedelta(seconds=3)).isoformat(),
            "run_id": run_id,
            "cycle_id": "cycle-grtc-c1",
            "order_count": 2,
            "fill_count": 2,
            "gross_alpha_pnl_usd": 100.0,
            "net_shadow_pnl_usd": 95.0,
            "execution_drag_usd": 5.0,
            "slippage_drag_usd": 2.0,
            "fee_drag_usd": 1.0,
            "latency_drag_usd": 2.0,
        },
    )
    CONTAINER.runtime_store.append(
        "execution_plans",
        [
            {
                "plan_id": "plan-maker-c1",
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
                "plan_id": "plan-taker-c1",
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
                "fill_id": "fill-maker-c1",
                "created_at": (now + timedelta(seconds=3)).isoformat(),
                "run_id": run_id,
                "mode": "shadow",
                "plan_id": "plan-maker-c1",
                "order_id": "order-maker-c1",
                "client_order_id": "client-maker-c1",
                "strategy_id": "strategy-c1",
                "alpha_family": "trend",
                "symbol": "BTCUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 200.0,
                "slippage_bps": 1.5,
                "latency_ms": 18.0,
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
                "fill_id": "fill-taker-c1",
                "created_at": (now + timedelta(seconds=4)).isoformat(),
                "run_id": run_id,
                "mode": "shadow",
                "plan_id": "plan-taker-c1",
                "order_id": "order-taker-c1",
                "client_order_id": "client-taker-c1",
                "strategy_id": "strategy-c1",
                "alpha_family": "trend",
                "symbol": "ETHUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 300.0,
                "slippage_bps": 4.5,
                "latency_ms": 32.0,
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

    payload = GovernanceRuntimeControlService().routing_control_latest()
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")
    if payload.get("run_id") != run_id:
        failures.append("run_id_mismatch")
    if payload.get("mode") != "shadow":
        failures.append("mode_mismatch")

    items = payload.get("items", [])
    if len(items) != 2:
        failures.append("route_decision_count_mismatch")

    by_route = {str(item.get("route") or ""): item for item in items}
    maker = by_route.get("maker_bias")
    taker = by_route.get("taker_primary")
    if maker is None:
        failures.append("maker_route_missing")
    if taker is None:
        failures.append("taker_route_missing")

    for item in items:
        for key in [
            "route",
            "avg_slippage_bps",
            "avg_latency_ms",
            "execution_drag_usd",
            "decision",
            "reason",
            "target_weight_multiplier",
        ]:
            if key not in item:
                failures.append(f"row_missing:{item.get('route')}:{key}")

    if maker and maker.get("decision") != "allow":
        failures.append("maker_route_should_allow")
    if taker and taker.get("decision") != "block":
        failures.append("taker_route_should_block")
    if maker and float(maker.get("target_weight_multiplier", -1.0)) != 1.0:
        failures.append("maker_multiplier_invalid")
    if taker and float(taker.get("target_weight_multiplier", -1.0)) != 0.0:
        failures.append("taker_multiplier_invalid")

    summary = payload.get("decision_summary") or {}
    if int(summary.get("allowed_routes", -1) or -1) != 1:
        failures.append("allowed_route_count_invalid")
    if int(summary.get("blocked_routes", -1) or -1) != 1:
        failures.append("blocked_route_count_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
