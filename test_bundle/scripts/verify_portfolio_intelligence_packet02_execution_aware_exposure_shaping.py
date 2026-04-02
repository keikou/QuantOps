from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Portfolio_intelligence_packet02_execution_aware_exposure_shaping_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-pi02-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def _reset_runtime_state(container, execution_routes, portfolio_routes) -> None:
    execution_routes._execution_quality_summary_cache["expires_at"] = None
    execution_routes._execution_quality_summary_cache["payload"] = None
    portfolio_routes._portfolio_overview_cache["expires_at"] = None
    portfolio_routes._portfolio_overview_cache["payload"] = None
    portfolio_routes._portfolio_overview_summary_cache["expires_at"] = None
    portfolio_routes._portfolio_overview_summary_cache["payload"] = None
    portfolio_routes._portfolio_positions_cache["expires_at"] = None
    portfolio_routes._portfolio_positions_cache["payload"] = None
    for table in [
        "execution_quality_snapshots",
        "execution_plans",
        "execution_fills",
        "shadow_pnl_snapshots",
        "audit_logs",
        "equity_snapshots",
        "position_snapshots_latest",
        "market_prices_latest",
    ]:
        try:
            container.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def _seed_portfolio(container, *, now: datetime) -> None:
    container.runtime_store.append(
        "equity_snapshots",
        {
            "snapshot_time": (now + timedelta(seconds=6)).isoformat(),
            "total_equity": 1000.0,
            "cash_balance": 300.0,
            "free_cash": 300.0,
            "used_margin": 100.0,
            "collateral_equity": 400.0,
            "available_margin": 200.0,
            "margin_utilization": 0.1,
            "gross_exposure": 700.0,
            "net_exposure": 700.0,
            "long_exposure": 700.0,
            "short_exposure": 0.0,
            "market_value": 1000.0,
            "realized_pnl": 10.0,
            "unrealized_pnl": -5.0,
            "fees_paid": 2.0,
            "drawdown": 0.03,
            "peak_equity": 1030.0,
        },
    )
    container.runtime_store.append(
        "position_snapshots_latest",
        [
            {
                "updated_at": (now + timedelta(seconds=6)).isoformat(),
                "symbol": "BTCUSDT",
                "strategy_id": "pi02",
                "alpha_family": "trend",
                "signed_qty": 1.0,
                "abs_qty": 1.0,
                "side": "long",
                "avg_entry_price": 100.0,
                "mark_price": 100.0,
                "market_value": 100.0,
                "realized_pnl": 0.0,
                "exposure_notional": 100.0,
                "unrealized_pnl": 0.5,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=6)).isoformat(),
                "quote_age_sec": 0.1,
                "stale": 0,
            },
            {
                "updated_at": (now + timedelta(seconds=6)).isoformat(),
                "symbol": "ETHUSDT",
                "strategy_id": "pi02",
                "alpha_family": "trend",
                "signed_qty": 1.0,
                "abs_qty": 1.0,
                "side": "long",
                "avg_entry_price": 900.0,
                "mark_price": 900.0,
                "market_value": 900.0,
                "realized_pnl": 0.0,
                "exposure_notional": 900.0,
                "unrealized_pnl": -1.0,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=6)).isoformat(),
                "quote_age_sec": 0.1,
                "stale": 0,
            },
        ],
    )


def _seed_run(container, *, now: datetime, run_id: str, cycle_id: str) -> None:
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
            "avg_slippage_bps": 2.2,
            "latency_ms_p50": 40.0,
            "latency_ms_p95": 95.0,
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
                "limit_price": 100.0,
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
                "limit_price": 900.0,
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
                "strategy_id": "strategy-pi02",
                "alpha_family": "trend",
                "symbol": "BTCUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 100.0,
                "slippage_bps": 1.0,
                "latency_ms": 95.0,
                "fee_bps": 1.0,
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
                "fill_id": f"fill-taker-{run_id}",
                "created_at": (now + timedelta(seconds=5)).isoformat(),
                "run_id": run_id,
                "mode": "shadow",
                "plan_id": f"plan-taker-{run_id}",
                "order_id": f"order-taker-{run_id}",
                "client_order_id": f"client-taker-{run_id}",
                "strategy_id": "strategy-pi02",
                "alpha_family": "trend",
                "symbol": "ETHUSDT",
                "side": "buy",
                "fill_qty": 1.0,
                "fill_price": 900.0,
                "slippage_bps": 3.2,
                "latency_ms": 40.0,
                "fee_bps": 1.0,
                "bid": 899.9,
                "ask": 900.1,
                "arrival_mid_price": 900.0,
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
        failures.append("missing_pi02_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/portfolio/intelligence/exposure-shaping/latest",
            "target_gross_exposure",
            "target_net_exposure",
            "target_weight_after_control",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.app.container import CONTAINER
    from ai_hedge_bot.api.routes import execution as execution_routes
    from ai_hedge_bot.api.routes import portfolio as portfolio_routes
    from ai_hedge_bot.services.governance_runtime_control_service import GovernanceRuntimeControlService
    from ai_hedge_bot.services.portfolio_intelligence_service import PortfolioIntelligenceService

    _reset_runtime_state(CONTAINER, execution_routes, portfolio_routes)
    governance = GovernanceRuntimeControlService()
    service = PortfolioIntelligenceService()
    now = datetime.now(timezone.utc)

    container = CONTAINER
    container.runtime_store.append(
        "execution_quality_snapshots",
        {
            "snapshot_id": "snap-pi02-prev",
            "created_at": (now + timedelta(seconds=1)).isoformat(),
            "run_id": "run-pi02-prev",
            "cycle_id": "cycle-pi02-prev",
            "mode": "shadow",
            "order_count": 2,
            "fill_count": 2,
            "fill_rate": 1.0,
            "avg_slippage_bps": 2.7,
            "latency_ms_p50": 20.0,
            "latency_ms_p95": 20.0,
        },
    )
    container.runtime_store.append(
        "shadow_pnl_snapshots",
        {
            "snapshot_id": "spnl-pi02-prev",
            "created_at": (now + timedelta(seconds=2)).isoformat(),
            "run_id": "run-pi02-prev",
            "cycle_id": "cycle-pi02-prev",
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
            {"plan_id": "plan-maker-prev", "created_at": (now + timedelta(seconds=1)).isoformat(), "run_id": "run-pi02-prev", "mode": "shadow", "symbol": "BTCUSDT", "side": "buy", "target_weight": 0.1, "order_qty": 1.0, "limit_price": 100.0, "participation_rate": 0.1, "status": "planned", "algo": "twap", "route": "maker_bias", "expire_seconds": 120, "slice_count": 1, "metadata_json": "{}"},
            {"plan_id": "plan-taker-prev", "created_at": (now + timedelta(seconds=1)).isoformat(), "run_id": "run-pi02-prev", "mode": "shadow", "symbol": "ETHUSDT", "side": "buy", "target_weight": 0.1, "order_qty": 1.0, "limit_price": 900.0, "participation_rate": 0.1, "status": "planned", "algo": "twap", "route": "taker_primary", "expire_seconds": 120, "slice_count": 1, "metadata_json": "{}"},
        ],
    )
    container.runtime_store.append(
        "execution_fills",
        [
            {"fill_id": "fill-maker-prev", "created_at": (now + timedelta(seconds=2)).isoformat(), "run_id": "run-pi02-prev", "mode": "shadow", "plan_id": "plan-maker-prev", "order_id": "order-maker-prev", "client_order_id": "client-maker-prev", "strategy_id": "strategy-pi02", "alpha_family": "trend", "symbol": "BTCUSDT", "side": "buy", "fill_qty": 1.0, "fill_price": 100.0, "slippage_bps": 2.6, "latency_ms": 20.0, "fee_bps": 1.0, "bid": 99.9, "ask": 100.1, "arrival_mid_price": 100.0, "price_source": "quote_test", "quote_time": (now + timedelta(seconds=2)).isoformat(), "quote_age_sec": 0.1, "fallback_reason": None, "status": "filled"},
            {"fill_id": "fill-taker-prev", "created_at": (now + timedelta(seconds=3)).isoformat(), "run_id": "run-pi02-prev", "mode": "shadow", "plan_id": "plan-taker-prev", "order_id": "order-taker-prev", "client_order_id": "client-taker-prev", "strategy_id": "strategy-pi02", "alpha_family": "trend", "symbol": "ETHUSDT", "side": "buy", "fill_qty": 1.0, "fill_price": 900.0, "slippage_bps": 2.6, "latency_ms": 20.0, "fee_bps": 1.0, "bid": 899.9, "ask": 900.1, "arrival_mid_price": 900.0, "price_source": "quote_test", "quote_time": (now + timedelta(seconds=3)).isoformat(), "quote_age_sec": 0.1, "fallback_reason": None, "status": "filled"},
        ],
    )
    governance.apply_closed_loop_adaptive_control_latest()
    for table in ["execution_quality_snapshots", "execution_plans", "execution_fills", "shadow_pnl_snapshots"]:
        container.runtime_store.execute(f"DELETE FROM {table}")
    execution_routes._execution_quality_summary_cache["expires_at"] = None
    execution_routes._execution_quality_summary_cache["payload"] = None

    _seed_run(container, now=now + timedelta(minutes=1), run_id="run-pi02-next", cycle_id="cycle-pi02-next")
    _seed_portfolio(container, now=now + timedelta(minutes=1))

    payload = service.execution_aware_exposure_shaping_latest()
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")
    if payload.get("run_id") != "run-pi02-next":
        failures.append("run_id_mismatch")
    if payload.get("cycle_id") != "cycle-pi02-next":
        failures.append("cycle_id_mismatch")

    items = payload.get("items", [])
    if len(items) != 2:
        failures.append("item_count_mismatch")
    by_symbol = {str(item.get("symbol") or ""): item for item in items}
    btc = by_symbol.get("BTCUSDT")
    eth = by_symbol.get("ETHUSDT")
    if btc is None:
        failures.append("btc_missing")
    if eth is None:
        failures.append("eth_missing")

    if btc and float(btc.get("target_weight_after_control", -1.0)) != 0.0:
        failures.append("btc_target_weight_invalid")
    if eth and float(eth.get("target_weight_after_control", -1.0)) != 0.0:
        failures.append("eth_target_weight_invalid")

    if float(payload.get("target_gross_exposure", -1.0)) != 0.0:
        failures.append("target_gross_exposure_invalid")
    if float(payload.get("target_net_exposure", -1.0)) != 0.0:
        failures.append("target_net_exposure_invalid")

    summary = payload.get("decision_summary") or {}
    if int(summary.get("symbol_count", -1)) != 2:
        failures.append("summary_symbol_count_invalid")
    if int(summary.get("zero_weight_symbols", -1)) != 2:
        failures.append("summary_zero_weight_symbols_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
