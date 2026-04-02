from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Portfolio_intelligence_packet05_allocation_outcome_effectiveness_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-pi05-", dir=str(REPO_ROOT / "runtime")))

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


def _seed_portfolio(
    container,
    *,
    now: datetime,
    btc_notional: float,
    eth_notional: float,
    sol_notional: float,
) -> None:
    total_equity = 1000.0
    container.runtime_store.append(
        "equity_snapshots",
        {
            "snapshot_time": (now + timedelta(seconds=8)).isoformat(),
            "total_equity": total_equity,
            "cash_balance": max(0.0, total_equity - (btc_notional + eth_notional + sol_notional)),
            "free_cash": max(0.0, total_equity - (btc_notional + eth_notional + sol_notional)),
            "used_margin": 100.0,
            "collateral_equity": 300.0,
            "available_margin": 200.0,
            "margin_utilization": 0.1,
            "gross_exposure": btc_notional + eth_notional + sol_notional,
            "net_exposure": btc_notional + eth_notional + sol_notional,
            "long_exposure": btc_notional + eth_notional + sol_notional,
            "short_exposure": 0.0,
            "market_value": total_equity,
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
                "strategy_id": "pi05",
                "alpha_family": "trend",
                "signed_qty": 1.0,
                "abs_qty": 1.0,
                "side": "long",
                "avg_entry_price": btc_notional,
                "mark_price": btc_notional,
                "market_value": btc_notional,
                "realized_pnl": 0.0,
                "exposure_notional": btc_notional,
                "unrealized_pnl": 1.0,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=8)).isoformat(),
                "quote_age_sec": 0.1,
                "stale": 0,
            },
            {
                "updated_at": (now + timedelta(seconds=8)).isoformat(),
                "symbol": "ETHUSDT",
                "strategy_id": "pi05",
                "alpha_family": "trend",
                "signed_qty": 1.0,
                "abs_qty": 1.0,
                "side": "long",
                "avg_entry_price": eth_notional,
                "mark_price": eth_notional,
                "market_value": eth_notional,
                "realized_pnl": 0.0,
                "exposure_notional": eth_notional,
                "unrealized_pnl": -1.0,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=8)).isoformat(),
                "quote_age_sec": 0.1,
                "stale": 0,
            },
            {
                "updated_at": (now + timedelta(seconds=8)).isoformat(),
                "symbol": "SOLUSDT",
                "strategy_id": "pi05",
                "alpha_family": "trend",
                "signed_qty": 1.0,
                "abs_qty": 1.0,
                "side": "long",
                "avg_entry_price": sol_notional,
                "mark_price": sol_notional,
                "market_value": sol_notional,
                "realized_pnl": 0.0,
                "exposure_notional": sol_notional,
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
    btc_price: float,
    eth_price: float,
    sol_price: float,
    btc_latency_ms: float,
    eth_slippage_bps: float,
    sol_slippage_bps: float,
) -> None:
    container.runtime_store.append(
        "execution_quality_snapshots",
        {
            "snapshot_id": f"snap-{run_id}",
            "created_at": (now + timedelta(seconds=3)).isoformat(),
            "run_id": run_id,
            "cycle_id": cycle_id,
            "mode": "shadow",
            "order_count": 3,
            "fill_count": 3,
            "fill_rate": 1.0,
            "avg_slippage_bps": max(1.2, (1.2 + eth_slippage_bps + sol_slippage_bps) / 3.0),
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
            "order_count": 3,
            "fill_count": 3,
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
            {"plan_id": f"plan-btc-{run_id}", "created_at": created_at, "run_id": run_id, "mode": "shadow", "symbol": "BTCUSDT", "side": "buy", "target_weight": 0.1, "order_qty": 1.0, "limit_price": btc_price, "participation_rate": 0.1, "status": "planned", "algo": "twap", "route": "maker_bias", "expire_seconds": 120, "slice_count": 1, "metadata_json": "{}"},
            {"plan_id": f"plan-eth-{run_id}", "created_at": created_at, "run_id": run_id, "mode": "shadow", "symbol": "ETHUSDT", "side": "buy", "target_weight": 0.1, "order_qty": 1.0, "limit_price": eth_price, "participation_rate": 0.1, "status": "planned", "algo": "twap", "route": "taker_primary", "expire_seconds": 120, "slice_count": 1, "metadata_json": "{}"},
            {"plan_id": f"plan-sol-{run_id}", "created_at": created_at, "run_id": run_id, "mode": "shadow", "symbol": "SOLUSDT", "side": "buy", "target_weight": 0.1, "order_qty": 1.0, "limit_price": sol_price, "participation_rate": 0.1, "status": "planned", "algo": "twap", "route": "maker_secondary", "expire_seconds": 120, "slice_count": 1, "metadata_json": "{}"},
        ],
    )
    container.runtime_store.append(
        "execution_fills",
        [
            {"fill_id": f"fill-btc-{run_id}", "created_at": (now + timedelta(seconds=4)).isoformat(), "run_id": run_id, "mode": "shadow", "plan_id": f"plan-btc-{run_id}", "order_id": f"order-btc-{run_id}", "client_order_id": f"client-btc-{run_id}", "strategy_id": "strategy-pi05", "alpha_family": "trend", "symbol": "BTCUSDT", "side": "buy", "fill_qty": 1.0, "fill_price": btc_price, "slippage_bps": 1.2, "latency_ms": btc_latency_ms, "fee_bps": 1.0, "bid": btc_price - 0.1, "ask": btc_price + 0.1, "arrival_mid_price": btc_price, "price_source": "quote_test", "quote_time": (now + timedelta(seconds=4)).isoformat(), "quote_age_sec": 0.1, "fallback_reason": None, "status": "filled"},
            {"fill_id": f"fill-eth-{run_id}", "created_at": (now + timedelta(seconds=5)).isoformat(), "run_id": run_id, "mode": "shadow", "plan_id": f"plan-eth-{run_id}", "order_id": f"order-eth-{run_id}", "client_order_id": f"client-eth-{run_id}", "strategy_id": "strategy-pi05", "alpha_family": "trend", "symbol": "ETHUSDT", "side": "buy", "fill_qty": 1.0, "fill_price": eth_price, "slippage_bps": eth_slippage_bps, "latency_ms": 35.0, "fee_bps": 1.0, "bid": eth_price - 0.1, "ask": eth_price + 0.1, "arrival_mid_price": eth_price, "price_source": "quote_test", "quote_time": (now + timedelta(seconds=5)).isoformat(), "quote_age_sec": 0.1, "fallback_reason": None, "status": "filled"},
            {"fill_id": f"fill-sol-{run_id}", "created_at": (now + timedelta(seconds=6)).isoformat(), "run_id": run_id, "mode": "shadow", "plan_id": f"plan-sol-{run_id}", "order_id": f"order-sol-{run_id}", "client_order_id": f"client-sol-{run_id}", "strategy_id": "strategy-pi05", "alpha_family": "trend", "symbol": "SOLUSDT", "side": "buy", "fill_qty": 1.0, "fill_price": sol_price, "slippage_bps": sol_slippage_bps, "latency_ms": 18.0, "fee_bps": 1.0, "bid": sol_price - 0.1, "ask": sol_price + 0.1, "arrival_mid_price": sol_price, "price_source": "quote_test", "quote_time": (now + timedelta(seconds=6)).isoformat(), "quote_age_sec": 0.1, "fallback_reason": None, "status": "filled"},
        ],
    )


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_pi05_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/portfolio/intelligence/allocation-outcome-effectiveness/latest",
            "previous_resolved_allocation_action",
            "intended_objective",
            "realized_effect",
            "policy_effectiveness_summary",
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
        run_id="run-pi05-prev",
        cycle_id="cycle-pi05-prev",
        btc_price=400.0,
        eth_price=250.0,
        sol_price=350.0,
        btc_latency_ms=20.0,
        eth_slippage_bps=3.4,
        sol_slippage_bps=1.1,
    )
    _seed_portfolio(CONTAINER, now=now, btc_notional=400.0, eth_notional=250.0, sol_notional=350.0)

    _seed_run(
        CONTAINER,
        now=now + timedelta(minutes=1),
        run_id="run-pi05-next",
        cycle_id="cycle-pi05-next",
        btc_price=500.0,
        eth_price=150.0,
        sol_price=350.0,
        btc_latency_ms=18.0,
        eth_slippage_bps=2.0,
        sol_slippage_bps=1.1,
    )
    _seed_portfolio(CONTAINER, now=now + timedelta(minutes=1), btc_notional=500.0, eth_notional=150.0, sol_notional=350.0)

    payload = service.allocation_outcome_effectiveness_latest()
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")
    if payload.get("run_id") != "run-pi05-next":
        failures.append("run_id_mismatch")
    if payload.get("previous_run_id") != "run-pi05-prev":
        failures.append("previous_run_id_mismatch")

    by_symbol = {str(item.get("symbol") or ""): item for item in list(payload.get("items") or [])}
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
        if btc.get("previous_resolved_allocation_action") != "trim":
            failures.append("btc_previous_action_invalid")
        if btc.get("realized_effect") != "adverse":
            failures.append("btc_realized_effect_invalid")
        if float(btc.get("drag_change_usd", 0.0) or 0.0) <= 0.0:
            failures.append("btc_drag_change_invalid")
        if btc.get("intended_objective") != "reduce_drag_or_concentration":
            failures.append("btc_objective_invalid")

    if eth:
        if eth.get("previous_resolved_allocation_action") != "trim":
            failures.append("eth_previous_action_invalid")
        if eth.get("realized_effect") != "beneficial":
            failures.append("eth_realized_effect_invalid")
        if float(eth.get("drag_change_usd", 0.0) or 0.0) >= 0.0:
            failures.append("eth_drag_change_invalid")
        if eth.get("intended_objective") != "reduce_drag_or_concentration":
            failures.append("eth_objective_invalid")

    if sol:
        if sol.get("previous_resolved_allocation_action") != "trim":
            failures.append("sol_previous_action_invalid")
        if sol.get("realized_effect") != "neutral":
            failures.append("sol_realized_effect_invalid")
        if sol.get("intended_objective") != "reduce_drag_or_concentration":
            failures.append("sol_objective_invalid")
        if abs(float(sol.get("resolved_weight_change", 999.0) if sol.get("resolved_weight_change", None) is not None else 999.0)) > 1e-9:
            failures.append("sol_weight_change_invalid")

    summary = payload.get("policy_effectiveness_summary") or {}
    if int(summary.get("symbol_count", -1)) < 3:
        failures.append("summary_symbol_count_invalid")
    if int(summary.get("beneficial_actions", -1)) < 1:
        failures.append("summary_beneficial_invalid")
    if int(summary.get("neutral_actions", -1)) < 1:
        failures.append("summary_neutral_invalid")
    if int(summary.get("adverse_actions", -1)) < 1:
        failures.append("summary_adverse_invalid")
    if float(summary.get("beneficial_ratio", -1.0) or -1.0) <= 0.0:
        failures.append("summary_beneficial_ratio_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
