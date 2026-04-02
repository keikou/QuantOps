from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Portfolio_intelligence_packet04_allocation_tradeoff_resolution_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-pi04-", dir=str(REPO_ROOT / "runtime")))

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
            "snapshot_time": (now + timedelta(seconds=8)).isoformat(),
            "total_equity": 1000.0,
            "cash_balance": 200.0,
            "free_cash": 200.0,
            "used_margin": 100.0,
            "collateral_equity": 300.0,
            "available_margin": 200.0,
            "margin_utilization": 0.1,
            "gross_exposure": 1000.0,
            "net_exposure": 1000.0,
            "long_exposure": 1000.0,
            "short_exposure": 0.0,
            "market_value": 1000.0,
            "realized_pnl": 15.0,
            "unrealized_pnl": -3.0,
            "fees_paid": 2.5,
            "drawdown": 0.02,
            "peak_equity": 1020.0,
        },
    )
    container.runtime_store.append(
        "position_snapshots_latest",
        [
            {
                "updated_at": (now + timedelta(seconds=8)).isoformat(),
                "symbol": "BTCUSDT",
                "strategy_id": "pi04",
                "alpha_family": "trend",
                "signed_qty": 1.0,
                "abs_qty": 1.0,
                "side": "long",
                "avg_entry_price": 400.0,
                "mark_price": 400.0,
                "market_value": 400.0,
                "realized_pnl": 0.0,
                "exposure_notional": 400.0,
                "unrealized_pnl": 1.0,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=8)).isoformat(),
                "quote_age_sec": 0.1,
                "stale": 0,
            },
            {
                "updated_at": (now + timedelta(seconds=8)).isoformat(),
                "symbol": "ETHUSDT",
                "strategy_id": "pi04",
                "alpha_family": "trend",
                "signed_qty": 1.0,
                "abs_qty": 1.0,
                "side": "long",
                "avg_entry_price": 250.0,
                "mark_price": 250.0,
                "market_value": 250.0,
                "realized_pnl": 0.0,
                "exposure_notional": 250.0,
                "unrealized_pnl": -1.0,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=8)).isoformat(),
                "quote_age_sec": 0.1,
                "stale": 0,
            },
            {
                "updated_at": (now + timedelta(seconds=8)).isoformat(),
                "symbol": "SOLUSDT",
                "strategy_id": "pi04",
                "alpha_family": "trend",
                "signed_qty": 1.0,
                "abs_qty": 1.0,
                "side": "long",
                "avg_entry_price": 350.0,
                "mark_price": 350.0,
                "market_value": 350.0,
                "realized_pnl": 0.0,
                "exposure_notional": 350.0,
                "unrealized_pnl": 0.5,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=8)).isoformat(),
                "quote_age_sec": 0.1,
                "stale": 0,
            },
        ],
    )


def _seed_run(
    container,
    *,
    now: datetime,
    run_id: str,
    cycle_id: str,
    btc_latency_ms: float,
    eth_slippage_bps: float,
) -> None:
    container.runtime_store.append(
        "execution_quality_snapshots",
        {
            "snapshot_id": f"snap-{run_id}",
            "created_at": (now + timedelta(seconds=3)).isoformat(),
            "run_id": run_id,
            "cycle_id": cycle_id,
            "mode": "shadow",
            "order_count": 4,
            "fill_count": 4,
            "fill_rate": 1.0,
            "avg_slippage_bps": 2.4,
            "latency_ms_p50": 20.0,
            "latency_ms_p95": max(40.0, btc_latency_ms),
        },
    )
    container.runtime_store.append(
        "shadow_pnl_snapshots",
        {
            "snapshot_id": f"spnl-{run_id}",
            "created_at": (now + timedelta(seconds=4)).isoformat(),
            "run_id": run_id,
            "cycle_id": cycle_id,
            "order_count": 4,
            "fill_count": 4,
            "gross_alpha_pnl_usd": 100.0,
            "net_shadow_pnl_usd": 95.0,
            "execution_drag_usd": 5.0,
            "slippage_drag_usd": 2.0,
            "fee_drag_usd": 1.0,
            "latency_drag_usd": 2.0,
        },
    )
    created_at = (now + timedelta(seconds=3)).isoformat()
    container.runtime_store.append(
        "execution_plans",
        [
            {"plan_id": f"plan-btc-{run_id}", "created_at": created_at, "run_id": run_id, "mode": "shadow", "symbol": "BTCUSDT", "side": "buy", "target_weight": 0.1, "order_qty": 1.0, "limit_price": 250.0, "participation_rate": 0.1, "status": "planned", "algo": "twap", "route": "maker_bias", "expire_seconds": 120, "slice_count": 1, "metadata_json": "{}"},
            {"plan_id": f"plan-eth-{run_id}", "created_at": created_at, "run_id": run_id, "mode": "shadow", "symbol": "ETHUSDT", "side": "buy", "target_weight": 0.1, "order_qty": 1.0, "limit_price": 400.0, "participation_rate": 0.1, "status": "planned", "algo": "twap", "route": "taker_primary", "expire_seconds": 120, "slice_count": 1, "metadata_json": "{}"},
            {"plan_id": f"plan-sol-{run_id}", "created_at": created_at, "run_id": run_id, "mode": "shadow", "symbol": "SOLUSDT", "side": "buy", "target_weight": 0.1, "order_qty": 1.0, "limit_price": 350.0, "participation_rate": 0.1, "status": "planned", "algo": "twap", "route": "maker_secondary", "expire_seconds": 120, "slice_count": 1, "metadata_json": "{}"},
            {"plan_id": f"plan-xrp-{run_id}", "created_at": created_at, "run_id": run_id, "mode": "shadow", "symbol": "XRPUSDT", "side": "buy", "target_weight": 0.1, "order_qty": 1.0, "limit_price": 200.0, "participation_rate": 0.1, "status": "planned", "algo": "twap", "route": "dummy_route", "expire_seconds": 120, "slice_count": 1, "metadata_json": "{}"},
        ],
    )
    container.runtime_store.append(
        "execution_fills",
        [
            {"fill_id": f"fill-btc-{run_id}", "created_at": (now + timedelta(seconds=4)).isoformat(), "run_id": run_id, "mode": "shadow", "plan_id": f"plan-btc-{run_id}", "order_id": f"order-btc-{run_id}", "client_order_id": f"client-btc-{run_id}", "strategy_id": "strategy-pi04", "alpha_family": "trend", "symbol": "BTCUSDT", "side": "buy", "fill_qty": 1.0, "fill_price": 250.0, "slippage_bps": 1.2, "latency_ms": btc_latency_ms, "fee_bps": 1.0, "bid": 249.9, "ask": 250.1, "arrival_mid_price": 250.0, "price_source": "quote_test", "quote_time": (now + timedelta(seconds=4)).isoformat(), "quote_age_sec": 0.1, "fallback_reason": None, "status": "filled"},
            {"fill_id": f"fill-eth-{run_id}", "created_at": (now + timedelta(seconds=5)).isoformat(), "run_id": run_id, "mode": "shadow", "plan_id": f"plan-eth-{run_id}", "order_id": f"order-eth-{run_id}", "client_order_id": f"client-eth-{run_id}", "strategy_id": "strategy-pi04", "alpha_family": "trend", "symbol": "ETHUSDT", "side": "buy", "fill_qty": 1.0, "fill_price": 400.0, "slippage_bps": eth_slippage_bps, "latency_ms": 35.0, "fee_bps": 1.0, "bid": 399.9, "ask": 400.1, "arrival_mid_price": 400.0, "price_source": "quote_test", "quote_time": (now + timedelta(seconds=5)).isoformat(), "quote_age_sec": 0.1, "fallback_reason": None, "status": "filled"},
            {"fill_id": f"fill-sol-{run_id}", "created_at": (now + timedelta(seconds=6)).isoformat(), "run_id": run_id, "mode": "shadow", "plan_id": f"plan-sol-{run_id}", "order_id": f"order-sol-{run_id}", "client_order_id": f"client-sol-{run_id}", "strategy_id": "strategy-pi04", "alpha_family": "trend", "symbol": "SOLUSDT", "side": "buy", "fill_qty": 1.0, "fill_price": 350.0, "slippage_bps": 1.1, "latency_ms": 18.0, "fee_bps": 1.0, "bid": 349.9, "ask": 350.1, "arrival_mid_price": 350.0, "price_source": "quote_test", "quote_time": (now + timedelta(seconds=6)).isoformat(), "quote_age_sec": 0.1, "fallback_reason": None, "status": "filled"},
            {"fill_id": f"fill-xrp-{run_id}", "created_at": (now + timedelta(seconds=7)).isoformat(), "run_id": run_id, "mode": "shadow", "plan_id": f"plan-xrp-{run_id}", "order_id": f"order-xrp-{run_id}", "client_order_id": f"client-xrp-{run_id}", "strategy_id": "strategy-pi04", "alpha_family": "trend", "symbol": "XRPUSDT", "side": "buy", "fill_qty": 1.0, "fill_price": 200.0, "slippage_bps": 1.0, "latency_ms": 15.0, "fee_bps": 1.0, "bid": 199.9, "ask": 200.1, "arrival_mid_price": 200.0, "price_source": "quote_test", "quote_time": (now + timedelta(seconds=7)).isoformat(), "quote_age_sec": 0.1, "fallback_reason": None, "status": "filled"},
        ],
    )


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_pi04_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/portfolio/intelligence/allocation-tradeoff/latest",
            "resolved_allocation_action",
            "tradeoff_breakdown",
            "tradeoff_reason_codes",
            "previous_resolved_allocation_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.app.container import CONTAINER
    from ai_hedge_bot.api.routes import execution as execution_routes
    from ai_hedge_bot.api.routes import portfolio as portfolio_routes
    from ai_hedge_bot.services.portfolio_intelligence_service import PortfolioIntelligenceService

    _reset_runtime_state(CONTAINER, execution_routes, portfolio_routes)
    service = PortfolioIntelligenceService()
    now = datetime.now(timezone.utc)

    _seed_run(
        CONTAINER,
        now=now,
        run_id="run-pi04-prev",
        cycle_id="cycle-pi04-prev",
        btc_latency_ms=95.0,
        eth_slippage_bps=1.6,
    )
    _seed_portfolio(CONTAINER, now=now)

    _seed_run(
        CONTAINER,
        now=now + timedelta(minutes=1),
        run_id="run-pi04-next",
        cycle_id="cycle-pi04-next",
        btc_latency_ms=20.0,
        eth_slippage_bps=3.4,
    )
    _seed_portfolio(CONTAINER, now=now + timedelta(minutes=1))

    payload = service.allocation_tradeoff_resolution_latest()
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")
    if payload.get("run_id") != "run-pi04-next":
        failures.append("run_id_mismatch")
    if payload.get("previous_run_id") != "run-pi04-prev":
        failures.append("previous_run_id_mismatch")

    items = payload.get("items", [])
    if len(items) < 4:
        failures.append("item_count_too_small")
    by_symbol = {str(item.get("symbol") or ""): item for item in items}

    btc = by_symbol.get("BTCUSDT")
    eth = by_symbol.get("ETHUSDT")
    sol = by_symbol.get("SOLUSDT")
    if btc is None:
        failures.append("btc_missing")
    if eth is None:
        failures.append("eth_missing")
    if sol is None:
        failures.append("sol_missing")

    if btc:
        if btc.get("resolved_allocation_action") != "increase":
            failures.append("btc_action_invalid")
        if btc.get("previous_resolved_allocation_action") != "zero":
            failures.append("btc_previous_action_invalid")
        if not bool(btc.get("action_changed")):
            failures.append("btc_action_changed_invalid")
        reasons = list(btc.get("tradeoff_reason_codes") or [])
        if "positive_delta_with_sufficient_score" not in reasons:
            failures.append("btc_reason_missing")

    if eth:
        if eth.get("resolved_allocation_action") != "trim":
            failures.append("eth_action_invalid")
        if eth.get("previous_resolved_allocation_action") not in {"increase", "hold", "trim"}:
            failures.append("eth_previous_action_invalid")
        breakdown = dict(eth.get("tradeoff_breakdown") or {})
        if float(breakdown.get("execution_penalty", 0.0) or 0.0) <= 0.0:
            failures.append("eth_execution_penalty_missing")
        if "negative_delta_or_penalty_pressure" not in list(eth.get("tradeoff_reason_codes") or []):
            failures.append("eth_reason_missing")

    if sol:
        if sol.get("resolved_allocation_action") != "hold":
            failures.append("sol_action_invalid")
        if float(sol.get("resolved_target_weight", -1.0) or -1.0) <= 0.0:
            failures.append("sol_target_weight_invalid")

    summary = payload.get("decision_summary") or {}
    if int(summary.get("increase_symbols", -1)) < 1:
        failures.append("summary_increase_invalid")
    if int(summary.get("trim_symbols", -1)) < 1:
        failures.append("summary_trim_invalid")
    if int(summary.get("hold_symbols", -1)) < 1:
        failures.append("summary_hold_invalid")
    if int(summary.get("changed_actions", -1)) < 1:
        failures.append("summary_changed_actions_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
