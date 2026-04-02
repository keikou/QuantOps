from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Governance_runtime_control_packet04_symbol_reallocation_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-grtc-c4-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def _reset_runtime_state(container, execution_routes) -> None:
    execution_routes._execution_quality_summary_cache["expires_at"] = None
    execution_routes._execution_quality_summary_cache["payload"] = None
    for table in [
        "execution_quality_snapshots",
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
        failures.append("missing_packet04_plan_doc")
    else:
        plan_text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/governance/runtime-control/symbol-reallocation/latest",
            "keep / trim / zero",
            "target_capital_multiplier",
            "symbol drag and notional concentration thresholds",
        ]:
            if needle not in plan_text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.app.container import CONTAINER
    from ai_hedge_bot.api.routes import execution as execution_routes
    from ai_hedge_bot.services.governance_runtime_control_service import GovernanceRuntimeControlService

    _reset_runtime_state(CONTAINER, execution_routes)

    now = datetime.now(timezone.utc)
    run_id = "run-grtc-c4"
    CONTAINER.runtime_store.append(
        "execution_quality_snapshots",
        {
            "snapshot_id": "snap-grtc-c4",
            "created_at": (now + timedelta(seconds=2)).isoformat(),
            "run_id": run_id,
            "cycle_id": "cycle-grtc-c4",
            "mode": "shadow",
            "order_count": 3,
            "fill_count": 3,
            "fill_rate": 1.0,
            "avg_slippage_bps": 3.0,
            "latency_ms_p50": 25.0,
            "latency_ms_p95": 45.0,
        },
    )
    CONTAINER.runtime_store.append(
        "shadow_pnl_snapshots",
        {
            "run_id": run_id,
            "created_at": (now + timedelta(seconds=3)).isoformat(),
            "gross_alpha_pnl_usd": 100.0,
            "net_shadow_pnl_usd": 88.0,
            "execution_drag_usd": 12.0,
            "slippage_drag_usd": 5.0,
            "fee_drag_usd": 4.0,
            "latency_drag_usd": 3.0,
        },
    )
    CONTAINER.runtime_store.append(
        "execution_fills",
        [
            {
                "fill_id": "fill-c4-keep",
                "created_at": (now + timedelta(seconds=3)).isoformat(),
                "run_id": run_id,
                "mode": "shadow",
                "plan_id": "plan-c4-keep",
                "order_id": "order-c4-keep",
                "client_order_id": "client-c4-keep",
                "strategy_id": "strategy-c4",
                "alpha_family": "trend",
                "symbol": "BTCUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 100.0,
                "slippage_bps": 1.0,
                "latency_ms": 20.0,
                "fee_bps": 1.0,
                "bid": 99.9,
                "ask": 100.1,
                "arrival_mid_price": 100.0,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=3)).isoformat(),
                "quote_age_sec": 0.1,
                "fallback_reason": None,
                "status": "filled",
            },
            {
                "fill_id": "fill-c4-trim",
                "created_at": (now + timedelta(seconds=4)).isoformat(),
                "run_id": run_id,
                "mode": "shadow",
                "plan_id": "plan-c4-trim",
                "order_id": "order-c4-trim",
                "client_order_id": "client-c4-trim",
                "strategy_id": "strategy-c4",
                "alpha_family": "trend",
                "symbol": "ETHUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 200.0,
                "slippage_bps": 3.0,
                "latency_ms": 25.0,
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
                "fill_id": "fill-c4-zero",
                "created_at": (now + timedelta(seconds=5)).isoformat(),
                "run_id": run_id,
                "mode": "shadow",
                "plan_id": "plan-c4-zero",
                "order_id": "order-c4-zero",
                "client_order_id": "client-c4-zero",
                "strategy_id": "strategy-c4",
                "alpha_family": "trend",
                "symbol": "SOLUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 500.0,
                "slippage_bps": 5.0,
                "latency_ms": 30.0,
                "fee_bps": 1.0,
                "bid": 499.9,
                "ask": 500.1,
                "arrival_mid_price": 500.0,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=5)).isoformat(),
                "quote_age_sec": 0.1,
                "fallback_reason": None,
                "status": "filled",
            },
        ],
    )

    payload = GovernanceRuntimeControlService().symbol_capital_reallocation_latest()
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")
    if payload.get("run_id") != run_id:
        failures.append("run_id_mismatch")
    if payload.get("mode") != "shadow":
        failures.append("mode_mismatch")

    items = payload.get("items", [])
    if len(items) != 3:
        failures.append("symbol_decision_count_mismatch")

    by_symbol = {str(item.get("symbol") or ""): item for item in items}
    keep_row = by_symbol.get("BTCUSDT")
    trim_row = by_symbol.get("ETHUSDT")
    zero_row = by_symbol.get("SOLUSDT")
    if keep_row is None:
        failures.append("keep_symbol_missing")
    if trim_row is None:
        failures.append("trim_symbol_missing")
    if zero_row is None:
        failures.append("zero_symbol_missing")

    for item in items:
        for key in [
            "symbol",
            "notional_share",
            "execution_drag_usd",
            "decision",
            "reason",
            "target_capital_multiplier",
        ]:
            if key not in item:
                failures.append(f"row_missing:{item.get('symbol')}:{key}")

    if keep_row and keep_row.get("decision") != "keep":
        failures.append("keep_symbol_should_keep")
    if trim_row and trim_row.get("decision") != "trim":
        failures.append("trim_symbol_should_trim")
    if zero_row and zero_row.get("decision") != "zero":
        failures.append("zero_symbol_should_zero")

    if keep_row and float(keep_row.get("target_capital_multiplier", -1.0)) != 1.0:
        failures.append("keep_multiplier_invalid")
    if trim_row and float(trim_row.get("target_capital_multiplier", -1.0)) != 0.5:
        failures.append("trim_multiplier_invalid")
    if zero_row and float(zero_row.get("target_capital_multiplier", -1.0)) != 0.0:
        failures.append("zero_multiplier_invalid")

    summary = payload.get("decision_summary") or {}
    if int(summary.get("kept_symbols", -1) or -1) != 1:
        failures.append("kept_symbol_count_invalid")
    if int(summary.get("trimmed_symbols", -1) or -1) != 1:
        failures.append("trimmed_symbol_count_invalid")
    if int(summary.get("zeroed_symbols", -1) or -1) != 1:
        failures.append("zeroed_symbol_count_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
