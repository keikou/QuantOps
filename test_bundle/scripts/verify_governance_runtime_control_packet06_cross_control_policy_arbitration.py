from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Governance_runtime_control_packet06_cross_control_policy_arbitration_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-grtc-c6-", dir=str(REPO_ROOT / "runtime")))

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
    quality_avg_slippage_bps: float,
    maker_slippage: float,
    maker_latency_ms: float,
    maker_fill_price: float,
    taker_slippage: float,
    taker_latency_ms: float,
    taker_fill_price: float,
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
            "avg_slippage_bps": quality_avg_slippage_bps,
            "latency_ms_p50": min(maker_latency_ms, taker_latency_ms),
            "latency_ms_p95": max(maker_latency_ms, taker_latency_ms),
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
                "limit_price": maker_fill_price,
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
                "limit_price": taker_fill_price,
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
                "strategy_id": "strategy-c6",
                "alpha_family": "trend",
                "symbol": "BTCUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": maker_fill_price,
                "slippage_bps": maker_slippage,
                "latency_ms": maker_latency_ms,
                "fee_bps": 1.0,
                "bid": maker_fill_price - 0.1,
                "ask": maker_fill_price + 0.1,
                "arrival_mid_price": maker_fill_price,
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
                "strategy_id": "strategy-c6",
                "alpha_family": "trend",
                "symbol": "ETHUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": taker_fill_price,
                "slippage_bps": taker_slippage,
                "latency_ms": taker_latency_ms,
                "fee_bps": 1.0,
                "bid": taker_fill_price - 0.1,
                "ask": taker_fill_price + 0.1,
                "arrival_mid_price": taker_fill_price,
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
        failures.append("missing_packet06_plan_doc")
    else:
        plan_text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/governance/runtime-control/policy-arbitration/latest",
            "/governance/runtime-control/policy-arbitration/apply",
            "resolved_runtime_action",
            "conflicts",
            "audit_logs",
            "halt",
            "stop",
            "block",
            "zero",
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
        run_id="run-grtc-c6-prev",
        cycle_id="cycle-grtc-c6-prev",
        quality_avg_slippage_bps=2.7,
        maker_slippage=2.6,
        maker_latency_ms=20.0,
        maker_fill_price=100.0,
        taker_slippage=2.6,
        taker_latency_ms=20.0,
        taker_fill_price=900.0,
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
        run_id="run-grtc-c6-next",
        cycle_id="cycle-grtc-c6-next",
        quality_avg_slippage_bps=2.2,
        maker_slippage=1.0,
        maker_latency_ms=95.0,
        maker_fill_price=100.0,
        taker_slippage=3.2,
        taker_latency_ms=40.0,
        taker_fill_price=900.0,
    )

    payload = service.cross_control_policy_arbitration_latest()
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")
    if payload.get("run_id") != "run-grtc-c6-next":
        failures.append("run_id_mismatch")
    if payload.get("cycle_id") != "cycle-grtc-c6-next":
        failures.append("cycle_id_mismatch")

    items = payload.get("items", [])
    if len(items) != 2:
        failures.append("route_count_mismatch")
    by_route = {str(item.get("route") or ""): item for item in items}
    maker = by_route.get("maker_bias")
    taker = by_route.get("taker_primary")
    if maker is None:
        failures.append("maker_route_missing")
    if taker is None:
        failures.append("taker_route_missing")

    for item in items:
        for key in [
            "resolved_runtime_action",
            "resolved_reason_set",
            "resolved_scope",
            "resolution_source_packet",
            "resolution_source",
            "raw_controls",
            "conflicts",
            "has_conflict",
            "cooldown_active",
        ]:
            if key not in item:
                failures.append(f"row_missing:{item.get('route')}:{key}")

    if maker:
        if maker.get("resolved_runtime_action") != "stop":
            failures.append("maker_resolved_action_invalid")
        if maker.get("resolution_source_packet") != "C3":
            failures.append("maker_resolution_source_packet_invalid")
        if maker.get("resolution_source") != "route_latency":
            failures.append("maker_resolution_source_invalid")
        if maker.get("resolved_scope") != "route":
            failures.append("maker_resolved_scope_invalid")
        raw_controls = maker.get("raw_controls") or {}
        if raw_controls.get("route_routing") != "degrade":
            failures.append("maker_route_routing_invalid")
        if raw_controls.get("route_latency") != "stop":
            failures.append("maker_route_latency_invalid")
        if raw_controls.get("symbol_capital") != "keep":
            failures.append("maker_symbol_capital_invalid")
        if raw_controls.get("route_adaptive") != "degrade":
            failures.append("maker_route_adaptive_invalid")
        if raw_controls.get("global_slippage_guard") != "continue":
            failures.append("maker_global_guard_invalid")
        if not maker.get("has_conflict"):
            failures.append("maker_conflict_not_visible")

    if taker:
        if taker.get("resolved_runtime_action") != "block":
            failures.append("taker_resolved_action_invalid")
        if taker.get("resolution_source_packet") != "C5":
            failures.append("taker_resolution_source_packet_invalid")
        if taker.get("resolution_source") != "route_adaptive":
            failures.append("taker_resolution_source_invalid")
        if taker.get("resolved_scope") != "route":
            failures.append("taker_resolved_scope_invalid")
        raw_controls = taker.get("raw_controls") or {}
        if raw_controls.get("route_routing") != "degrade":
            failures.append("taker_route_routing_invalid")
        if raw_controls.get("route_latency") != "throttle":
            failures.append("taker_route_latency_invalid")
        if raw_controls.get("symbol_capital") != "zero":
            failures.append("taker_symbol_capital_invalid")
        if raw_controls.get("route_adaptive") != "block":
            failures.append("taker_route_adaptive_invalid")
        if raw_controls.get("global_slippage_guard") != "continue":
            failures.append("taker_global_guard_invalid")
        if not taker.get("has_conflict"):
            failures.append("taker_conflict_not_visible")

    summary = payload.get("decision_summary") or {}
    if int(summary.get("route_count", -1)) != 2:
        failures.append("summary_route_count_invalid")
    if int(summary.get("conflicted_routes", -1)) != 2:
        failures.append("summary_conflicted_routes_invalid")
    if int(summary.get("global_halt_routes", -1)) != 0:
        failures.append("summary_global_halt_routes_invalid")
    if int(summary.get("blocking_routes", -1)) != 2:
        failures.append("summary_blocking_routes_invalid")

    precedence_order = payload.get("precedence_order") or []
    if precedence_order[:5] != ["halt", "stop", "block", "zero", "pause"]:
        failures.append("precedence_order_invalid")

    applied = service.apply_cross_control_policy_arbitration_latest()
    if applied.get("status") != "ok":
        failures.append("apply_status_not_ok")
    if int(applied.get("saved_resolution_count", -1)) != 2:
        failures.append("saved_resolution_count_invalid")

    audit_rows = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT event_type, actor, payload_json
        FROM audit_logs
        WHERE category = 'governance_runtime_control'
          AND event_type = 'policy_arbitration_resolution'
        ORDER BY created_at DESC
        """
    )
    if len(audit_rows) != 2:
        failures.append("audit_resolution_row_count_invalid")
    else:
        resolved_from_audit: dict[str, dict[str, object]] = {}
        for row in audit_rows:
            if row.get("event_type") != "policy_arbitration_resolution":
                failures.append("audit_event_type_invalid")
            if row.get("actor") != "governance_runtime_control":
                failures.append("audit_actor_invalid")
            payload_json = json.loads(str(row.get("payload_json") or "{}"))
            resolved_from_audit[str(payload_json.get("route") or "")] = payload_json
        if resolved_from_audit.get("maker_bias", {}).get("resolved_runtime_action") != "stop":
            failures.append("audit_maker_resolution_invalid")
        if resolved_from_audit.get("taker_primary", {}).get("resolved_runtime_action") != "block":
            failures.append("audit_taker_resolution_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
