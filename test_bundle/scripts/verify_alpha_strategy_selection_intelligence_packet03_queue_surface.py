from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Alpha_strategy_selection_intelligence_packet03_queue_surface_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-assi03-", dir=str(REPO_ROOT / "runtime")))

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


def _seed_portfolio(container, *, now: datetime, families: list[str], notionals: list[float]) -> None:
    total_equity = 1000.0
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    container.runtime_store.append(
        "equity_snapshots",
        {
            "snapshot_time": (now + timedelta(seconds=8)).isoformat(),
            "total_equity": total_equity,
            "cash_balance": max(0.0, total_equity - sum(notionals)),
            "free_cash": max(0.0, total_equity - sum(notionals)),
            "used_margin": 100.0,
            "collateral_equity": 300.0,
            "available_margin": 200.0,
            "margin_utilization": 0.1,
            "gross_exposure": sum(notionals),
            "net_exposure": sum(notionals),
            "long_exposure": sum(notionals),
            "short_exposure": 0.0,
            "market_value": total_equity,
            "realized_pnl": 15.0,
            "unrealized_pnl": -3.0,
            "fees_paid": 2.5,
            "drawdown": 0.02,
            "peak_equity": 1020.0,
        },
    )
    rows = []
    for symbol, family, notional in zip(symbols, families, notionals, strict=True):
        rows.append(
            {
                "updated_at": (now + timedelta(seconds=8)).isoformat(),
                "symbol": symbol,
                "strategy_id": "assi03",
                "alpha_family": family,
                "signed_qty": 1.0,
                "abs_qty": 1.0,
                "side": "long",
                "avg_entry_price": notional,
                "mark_price": notional,
                "market_value": notional,
                "realized_pnl": 0.0,
                "exposure_notional": notional,
                "unrealized_pnl": 1.0,
                "price_source": "quote_test",
                "quote_time": (now + timedelta(seconds=8)).isoformat(),
                "quote_age_sec": 0.1,
                "stale": 0,
            }
        )
    container.runtime_store.append("position_snapshots_latest", rows)


def _seed_run(
    container,
    *,
    now: datetime,
    run_id: str,
    cycle_id: str,
    avg_slippage_bps: float,
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
            "avg_slippage_bps": avg_slippage_bps,
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
            {"fill_id": f"fill-btc-{run_id}", "created_at": (now + timedelta(seconds=4)).isoformat(), "run_id": run_id, "mode": "shadow", "plan_id": f"plan-btc-{run_id}", "order_id": f"order-btc-{run_id}", "client_order_id": f"client-btc-{run_id}", "strategy_id": "strategy-assi03", "alpha_family": "x", "symbol": "BTCUSDT", "side": "buy", "fill_qty": 1.0, "fill_price": btc_price, "slippage_bps": 1.2, "latency_ms": btc_latency_ms, "fee_bps": 1.0, "bid": btc_price - 0.1, "ask": btc_price + 0.1, "arrival_mid_price": btc_price, "price_source": "quote_test", "quote_time": (now + timedelta(seconds=4)).isoformat(), "quote_age_sec": 0.1, "fallback_reason": None, "status": "filled"},
            {"fill_id": f"fill-eth-{run_id}", "created_at": (now + timedelta(seconds=5)).isoformat(), "run_id": run_id, "mode": "shadow", "plan_id": f"plan-eth-{run_id}", "order_id": f"order-eth-{run_id}", "client_order_id": f"client-eth-{run_id}", "strategy_id": "strategy-assi03", "alpha_family": "x", "symbol": "ETHUSDT", "side": "buy", "fill_qty": 1.0, "fill_price": eth_price, "slippage_bps": eth_slippage_bps, "latency_ms": 35.0, "fee_bps": 1.0, "bid": eth_price - 0.1, "ask": eth_price + 0.1, "arrival_mid_price": eth_price, "price_source": "quote_test", "quote_time": (now + timedelta(seconds=5)).isoformat(), "quote_age_sec": 0.1, "fallback_reason": None, "status": "filled"},
            {"fill_id": f"fill-sol-{run_id}", "created_at": (now + timedelta(seconds=6)).isoformat(), "run_id": run_id, "mode": "shadow", "plan_id": f"plan-sol-{run_id}", "order_id": f"order-sol-{run_id}", "client_order_id": f"client-sol-{run_id}", "strategy_id": "strategy-assi03", "alpha_family": "x", "symbol": "SOLUSDT", "side": "buy", "fill_qty": 1.0, "fill_price": sol_price, "slippage_bps": sol_slippage_bps, "latency_ms": 18.0, "fee_bps": 1.0, "bid": sol_price - 0.1, "ask": sol_price + 0.1, "arrival_mid_price": sol_price, "price_source": "quote_test", "quote_time": (now + timedelta(seconds=6)).isoformat(), "quote_age_sec": 0.1, "fallback_reason": None, "status": "filled"},
        ],
    )


def _choose_families(alpha_service) -> list[str]:
    ranking_rows = alpha_service.ranking(limit=10)
    selected: list[str] = []
    seen: set[str] = set()
    for row in ranking_rows:
        alpha_id = str(row.get("alpha_id") or "")
        meta = alpha_service._lookup_alpha(alpha_id) or {}
        family = str(meta.get("alpha_family") or "")
        if family and family not in seen:
            selected.append(family)
            seen.add(family)
        if len(selected) == 3:
            break
    return selected[:3]


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_assi03_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/alpha/intelligence/selection-queues/latest",
            "queue_name",
            "queue_priority",
            "queue_reason",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.app.container import CONTAINER
    from ai_hedge_bot.api.routes import execution as execution_routes
    from ai_hedge_bot.api.routes import portfolio as portfolio_routes
    from ai_hedge_bot.autonomous_alpha.service import AutonomousAlphaService
    from ai_hedge_bot.services.alpha_strategy_selection_intelligence_service import (
        AlphaStrategySelectionIntelligenceService,
    )

    _reset_runtime_state(CONTAINER, execution_routes, portfolio_routes)
    alpha_service = AutonomousAlphaService()
    families = _choose_families(alpha_service)
    if len(families) < 3:
        failures.append("not_enough_families")

    now = datetime.now(timezone.utc)
    _seed_run(
        CONTAINER,
        now=now,
        run_id="run-assi03-prev",
        cycle_id="cycle-assi03-prev",
        avg_slippage_bps=1.9,
        btc_price=400.0,
        eth_price=250.0,
        sol_price=350.0,
        btc_latency_ms=20.0,
        eth_slippage_bps=3.4,
        sol_slippage_bps=1.1,
    )
    _seed_portfolio(CONTAINER, now=now, families=families, notionals=[400.0, 250.0, 350.0])

    _seed_run(
        CONTAINER,
        now=now + timedelta(minutes=1),
        run_id="run-assi03-next",
        cycle_id="cycle-assi03-next",
        avg_slippage_bps=1.6,
        btc_price=500.0,
        eth_price=150.0,
        sol_price=350.0,
        btc_latency_ms=18.0,
        eth_slippage_bps=2.0,
        sol_slippage_bps=1.1,
    )
    _seed_portfolio(CONTAINER, now=now + timedelta(minutes=1), families=families, notionals=[500.0, 150.0, 350.0])

    service = AlphaStrategySelectionIntelligenceService()
    payload = service.selection_queue_latest(limit=10)

    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")
    if payload.get("run_id") != "run-assi03-next":
        failures.append("run_id_mismatch")

    items = list(payload.get("items") or [])
    if not items:
        failures.append("items_missing")

    top_by_family: dict[str, dict] = {}
    for item in items:
        family = str(item.get("alpha_family") or "")
        current = top_by_family.get(family)
        if current is None or float(item.get("selection_score", 0.0) or 0.0) > float(current.get("selection_score", 0.0) or 0.0):
            top_by_family[family] = item
        if str(item.get("queue_name") or "") not in {"promotion_candidate", "shadow_review", "research_return", "deferred_watchlist"}:
            failures.append("invalid_queue_name")
        if str(item.get("queue_priority") or "") not in {"highest", "high", "normal", "low"}:
            failures.append("invalid_queue_priority")

    btc_item = top_by_family.get(families[0]) if len(families) > 0 else None
    eth_item = top_by_family.get(families[1]) if len(families) > 1 else None
    sol_item = top_by_family.get(families[2]) if len(families) > 2 else None

    if btc_item and btc_item.get("queue_name") != "research_return":
        failures.append("btc_queue_invalid")
    if eth_item and eth_item.get("queue_name") != "shadow_review":
        failures.append("eth_queue_invalid")
    if sol_item and sol_item.get("queue_name") != "research_return":
        failures.append("sol_queue_invalid")

    summary = payload.get("decision_summary") or {}
    if int(summary.get("shadow_review_count", 0) or 0) < 1:
        failures.append("shadow_review_count_invalid")
    if int(summary.get("research_return_count", 0) or 0) < 1:
        failures.append("research_return_count_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
