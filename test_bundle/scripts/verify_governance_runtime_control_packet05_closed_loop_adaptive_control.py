from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Governance_runtime_control_packet05_closed_loop_adaptive_control_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-grtc-c5-", dir=str(REPO_ROOT / "runtime")))

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
        "audit_logs",
    ]:
        try:
            container.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def _seed_run(
    container,
    *,
    now: datetime,
    run_id: str,
    cycle_id: str,
    maker_slippage: float,
    taker_slippage: float,
) -> None:
    container.runtime_store.append(
        "execution_quality_snapshots",
        {
            "snapshot_id": f"snap-{run_id}",
            "created_at": (now + timedelta(seconds=3)).isoformat(),
            "run_id": run_id,
            "cycle_id": cycle_id,
            "mode": "shadow",
            "order_count": 2,
            "fill_count": 2,
            "fill_rate": 1.0,
            "avg_slippage_bps": round((maker_slippage + taker_slippage) / 2.0, 4),
            "latency_ms_p50": 20.0,
            "latency_ms_p95": 35.0,
        },
    )
    container.runtime_store.append(
        "shadow_pnl_snapshots",
        {
            "snapshot_id": f"spnl-{run_id}",
            "created_at": (now + timedelta(seconds=4)).isoformat(),
            "run_id": run_id,
            "cycle_id": cycle_id,
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
    container.runtime_store.append(
        "execution_plans",
        [
            {
                "plan_id": f"plan-maker-{run_id}",
                "created_at": (now + timedelta(seconds=3)).isoformat(),
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
                "plan_id": f"plan-taker-{run_id}",
                "created_at": (now + timedelta(seconds=3)).isoformat(),
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
    container.runtime_store.append(
        "execution_fills",
        [
            {
                "fill_id": f"fill-maker-{run_id}",
                "created_at": (now + timedelta(seconds=4)).isoformat(),
                "run_id": run_id,
                "mode": "shadow",
                "plan_id": f"plan-maker-{run_id}",
                "order_id": f"order-maker-{run_id}",
                "client_order_id": f"client-maker-{run_id}",
                "strategy_id": "strategy-c5",
                "alpha_family": "trend",
                "symbol": "BTCUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 200.0,
                "slippage_bps": maker_slippage,
                "latency_ms": 18.0,
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
                "fill_id": f"fill-taker-{run_id}",
                "created_at": (now + timedelta(seconds=5)).isoformat(),
                "run_id": run_id,
                "mode": "shadow",
                "plan_id": f"plan-taker-{run_id}",
                "order_id": f"order-taker-{run_id}",
                "client_order_id": f"client-taker-{run_id}",
                "strategy_id": "strategy-c5",
                "alpha_family": "trend",
                "symbol": "ETHUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 300.0,
                "slippage_bps": taker_slippage,
                "latency_ms": 20.0,
                "fee_bps": 1.0,
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


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_packet05_plan_doc")
    else:
        plan_text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/governance/runtime-control/closed-loop/latest",
            "/governance/runtime-control/closed-loop/apply",
            "relax",
            "escalate",
            "adaptive_target_weight_multiplier",
        ]:
            if needle not in plan_text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.app.container import CONTAINER
    from ai_hedge_bot.api.routes import execution as execution_routes
    from ai_hedge_bot.services.governance_runtime_control_service import GovernanceRuntimeControlService

    _reset_runtime_state(CONTAINER, execution_routes)
    service = GovernanceRuntimeControlService()
    now = datetime.now(timezone.utc)

    _seed_run(
        CONTAINER,
        now=now,
        run_id="run-grtc-c5-prev",
        cycle_id="cycle-grtc-c5-prev",
        maker_slippage=3.0,
        taker_slippage=3.1,
    )
    applied_prev = service.apply_closed_loop_adaptive_control_latest()
    if int(applied_prev.get("saved_feedback_count", 0) or 0) != 2:
        failures.append("previous_feedback_not_saved")

    for table in ["execution_quality_snapshots", "execution_plans", "execution_fills", "shadow_pnl_snapshots"]:
        CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
    execution_routes._execution_quality_summary_cache["expires_at"] = None
    execution_routes._execution_quality_summary_cache["payload"] = None

    _seed_run(
        CONTAINER,
        now=now + timedelta(minutes=1),
        run_id="run-grtc-c5-next",
        cycle_id="cycle-grtc-c5-next",
        maker_slippage=1.5,
        taker_slippage=3.8,
    )
    payload = service.closed_loop_adaptive_control_latest()

    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")
    if payload.get("run_id") != "run-grtc-c5-next":
        failures.append("run_id_mismatch")

    items = payload.get("items", [])
    if len(items) != 2:
        failures.append("adaptive_route_count_mismatch")
    by_route = {str(item.get("route") or ""): item for item in items}
    maker = by_route.get("maker_bias")
    taker = by_route.get("taker_primary")
    if maker is None:
        failures.append("maker_route_missing")
    if taker is None:
        failures.append("taker_route_missing")

    for item in items:
        for key in [
            "base_decision",
            "adapted_decision",
            "adaptation_state",
            "previous_decision",
            "previous_observed_slippage_bps",
            "delta_slippage_bps",
            "adaptive_target_weight_multiplier",
        ]:
            if key not in item:
                failures.append(f"row_missing:{item.get('route')}:{key}")

    if maker and maker.get("base_decision") != "allow":
        failures.append("maker_base_decision_invalid")
    if maker and maker.get("adapted_decision") != "allow":
        failures.append("maker_should_relax_to_allow")
    if maker and maker.get("adaptation_state") != "relax_after_improvement":
        failures.append("maker_relax_state_missing")
    if maker and float(maker.get("adaptive_target_weight_multiplier", -1.0)) != 1.0:
        failures.append("maker_adaptive_multiplier_invalid")

    if taker and taker.get("base_decision") != "degrade":
        failures.append("taker_base_decision_invalid")
    if taker and taker.get("adapted_decision") != "block":
        failures.append("taker_should_escalate_to_block")
    if taker and taker.get("adaptation_state") != "escalate_after_failed_degrade":
        failures.append("taker_escalate_state_missing")
    if taker and float(taker.get("adaptive_target_weight_multiplier", -1.0)) != 0.0:
        failures.append("taker_adaptive_multiplier_invalid")

    summary = payload.get("decision_summary") or {}
    if int(summary.get("adapted_routes", -1) or -1) != 2:
        failures.append("adapted_route_count_invalid")
    if int(summary.get("blocked_routes", -1) or -1) != 1:
        failures.append("blocked_route_count_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
