from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Research_promotion_intelligence_packet03_review_queues_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-rpi03-", dir=str(REPO_ROOT / "runtime")))

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
        "experiment_tracker",
        "model_registry",
        "model_state_transitions",
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
                "strategy_id": "rpi03",
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
            {"fill_id": f"fill-btc-{run_id}", "created_at": (now + timedelta(seconds=4)).isoformat(), "run_id": run_id, "mode": "shadow", "plan_id": f"plan-btc-{run_id}", "order_id": f"order-btc-{run_id}", "client_order_id": f"client-btc-{run_id}", "strategy_id": "strategy-rpi03", "alpha_family": "x", "symbol": "BTCUSDT", "side": "buy", "fill_qty": 1.0, "fill_price": btc_price, "slippage_bps": 1.2, "latency_ms": btc_latency_ms, "fee_bps": 1.0, "bid": btc_price - 0.1, "ask": btc_price + 0.1, "arrival_mid_price": btc_price, "price_source": "quote_test", "quote_time": (now + timedelta(seconds=4)).isoformat(), "quote_age_sec": 0.1, "fallback_reason": None, "status": "filled"},
            {"fill_id": f"fill-eth-{run_id}", "created_at": (now + timedelta(seconds=5)).isoformat(), "run_id": run_id, "mode": "shadow", "plan_id": f"plan-eth-{run_id}", "order_id": f"order-eth-{run_id}", "client_order_id": f"client-eth-{run_id}", "strategy_id": "strategy-rpi03", "alpha_family": "x", "symbol": "ETHUSDT", "side": "buy", "fill_qty": 1.0, "fill_price": eth_price, "slippage_bps": eth_slippage_bps, "latency_ms": 35.0, "fee_bps": 1.0, "bid": eth_price - 0.1, "ask": eth_price + 0.1, "arrival_mid_price": eth_price, "price_source": "quote_test", "quote_time": (now + timedelta(seconds=5)).isoformat(), "quote_age_sec": 0.1, "fallback_reason": None, "status": "filled"},
            {"fill_id": f"fill-sol-{run_id}", "created_at": (now + timedelta(seconds=6)).isoformat(), "run_id": run_id, "mode": "shadow", "plan_id": f"plan-sol-{run_id}", "order_id": f"order-sol-{run_id}", "client_order_id": f"client-sol-{run_id}", "strategy_id": "strategy-rpi03", "alpha_family": "x", "symbol": "SOLUSDT", "side": "buy", "fill_qty": 1.0, "fill_price": sol_price, "slippage_bps": sol_slippage_bps, "latency_ms": 18.0, "fee_bps": 1.0, "bid": sol_price - 0.1, "ask": sol_price + 0.1, "arrival_mid_price": sol_price, "price_source": "quote_test", "quote_time": (now + timedelta(seconds=6)).isoformat(), "quote_age_sec": 0.1, "fallback_reason": None, "status": "filled"},
        ],
    )


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_rpi03_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/research-factory/intelligence/review-queues/latest",
            "review_queue",
            "next_review_action",
            "research_backlog",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.app.container import CONTAINER
    from ai_hedge_bot.api.routes import execution as execution_routes
    from ai_hedge_bot.api.routes import portfolio as portfolio_routes
    from ai_hedge_bot.autonomous_alpha.service import AutonomousAlphaService
    from ai_hedge_bot.services.research_promotion_intelligence_service import (
        ResearchPromotionIntelligenceService,
    )

    _reset_runtime_state(CONTAINER, execution_routes, portfolio_routes)
    alpha_service = AutonomousAlphaService()
    now = datetime.now(timezone.utc)
    families = ["momentum", "mean_reversion", "derivatives"]

    alpha_service.store.append(
        "alpha_registry",
        {
            "alpha_id": "mean_reversion_peer_alpha",
            "created_at": (now - timedelta(minutes=10)).isoformat(),
            "alpha_family": "mean_reversion",
            "factor_type": "mean_reversion",
            "horizon": "short",
            "turnover_profile": "medium",
            "feature_dependencies_json": alpha_service.store.to_json(["mr_1"]),
            "risk_profile": "balanced",
            "execution_sensitivity": 0.18,
            "state": "candidate",
            "source": "rpi03_test",
            "notes": "review queue peer",
        },
    )
    alpha_service.store.append(
        "alpha_rankings",
        {
            "ranking_id": "rpi03-ranking-peer",
            "created_at": (now - timedelta(minutes=9)).isoformat(),
            "alpha_id": "mean_reversion_peer_alpha",
            "rank_score": 0.74,
            "expected_return": 0.09,
            "risk_adjusted_score": 0.72,
            "execution_cost_adjusted_score": 0.7,
            "diversification_value": 0.5,
            "recommended_action": "shadow",
        },
    )
    alpha_service.store.append(
        "alpha_registry",
        {
            "alpha_id": "promoted_weak_alpha",
            "created_at": (now - timedelta(minutes=11)).isoformat(),
            "alpha_family": "event",
            "factor_type": "event",
            "horizon": "short",
            "turnover_profile": "medium",
            "feature_dependencies_json": alpha_service.store.to_json(["event_1"]),
            "risk_profile": "balanced",
            "execution_sensitivity": 0.34,
            "state": "promoted",
            "source": "rpi03_test",
            "notes": "weak promoted alpha",
        },
    )
    alpha_service.store.append(
        "alpha_rankings",
        {
            "ranking_id": "rpi03-ranking-weak",
            "created_at": (now - timedelta(minutes=9)).isoformat(),
            "alpha_id": "promoted_weak_alpha",
            "rank_score": 0.29,
            "expected_return": 0.02,
            "risk_adjusted_score": 0.24,
            "execution_cost_adjusted_score": 0.2,
            "diversification_value": 0.35,
            "recommended_action": "research",
        },
    )

    _seed_run(
        CONTAINER,
        now=now,
        run_id="run-rpi03-prev",
        cycle_id="cycle-rpi03-prev",
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
        run_id="run-rpi03-next",
        cycle_id="cycle-rpi03-next",
        avg_slippage_bps=1.6,
        btc_price=500.0,
        eth_price=150.0,
        sol_price=350.0,
        btc_latency_ms=18.0,
        eth_slippage_bps=2.0,
        sol_slippage_bps=1.1,
    )
    _seed_portfolio(CONTAINER, now=now + timedelta(minutes=1), families=families, notionals=[500.0, 150.0, 350.0])

    store = CONTAINER.runtime_store
    created_at = (now + timedelta(minutes=2)).isoformat()
    store.append(
        "experiment_tracker",
        [
            {
                "experiment_id": "exp-rpi03-mr",
                "created_at": created_at,
                "dataset_version": "dataset.mr.v2",
                "feature_version": "features.mr.v2",
                "model_version": "model.mr.v2",
                "alpha_id": "mean_reversion_alpha",
                "strategy_id": "mr_core",
                "hypothesis": "mr alpha ready for shadow review",
                "hyperparameters_json": store.to_json({"lr": 0.03}),
                "validation_result_json": store.to_json({"walk_forward_sharpe": 1.4}),
                "notes": "seeded by verifier",
                "immutable_record": True,
            },
            {
                "experiment_id": "exp-rpi03-breakout",
                "created_at": created_at,
                "dataset_version": "dataset.breakout.v1",
                "feature_version": "features.breakout.v1",
                "model_version": "model.breakout.v1",
                "alpha_id": "breakout_alpha",
                "strategy_id": "breakout_core",
                "hypothesis": "breakout alpha should be retired",
                "hyperparameters_json": store.to_json({"lr": 0.01}),
                "validation_result_json": store.to_json({"walk_forward_sharpe": 0.35}),
                "notes": "seeded by verifier",
                "immutable_record": True,
            },
        ],
    )
    store.append(
        "model_registry",
        [
            {
                "model_id": "model-rpi03-mr",
                "created_at": created_at,
                "experiment_id": "exp-rpi03-mr",
                "dataset_version": "dataset.mr.v2",
                "feature_version": "features.mr.v2",
                "model_version": "model.mr.v2",
                "validation_metrics_json": store.to_json({"summary_score": 0.81}),
                "state": "shadow",
                "notes": "seeded by verifier",
            },
            {
                "model_id": "model-rpi03-breakout",
                "created_at": created_at,
                "experiment_id": "exp-rpi03-breakout",
                "dataset_version": "dataset.breakout.v1",
                "feature_version": "features.breakout.v1",
                "model_version": "model.breakout.v1",
                "validation_metrics_json": store.to_json({"summary_score": 0.25}),
                "state": "deprecated",
                "notes": "seeded by verifier",
            },
        ],
    )

    service = ResearchPromotionIntelligenceService()
    payload = service.review_queues_latest(limit=20)

    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")
    if payload.get("run_id") != "run-rpi03-next":
        failures.append("run_id_mismatch")

    by_alpha = {str(item.get("alpha_id") or ""): item for item in list(payload.get("items") or [])}

    if by_alpha.get("trend_alpha", {}).get("review_queue") != "research_backlog":
        failures.append("trend_should_be_research_backlog")
    if by_alpha.get("trend_alpha", {}).get("next_review_action") != "hold_for_more_evidence":
        failures.append("trend_next_action_invalid")
    if by_alpha.get("mean_reversion_alpha", {}).get("review_queue") != "shadow_review":
        failures.append("mean_reversion_should_be_shadow_review")
    if by_alpha.get("breakout_alpha", {}).get("review_queue") != "retirement_review":
        failures.append("breakout_should_be_retirement_review")
    if by_alpha.get("mean_reversion_peer_alpha", {}).get("review_queue") != "research_backlog":
        failures.append("peer_should_be_research_backlog")

    summary = payload.get("queue_summary") or {}
    if int(summary.get("shadow_review_count", 0) or 0) < 1:
        failures.append("shadow_review_count_invalid")
    if int(summary.get("retirement_review_count", 0) or 0) < 1:
        failures.append("retirement_review_count_invalid")
    if int(summary.get("research_backlog_count", 0) or 0) < 1:
        failures.append("research_backlog_count_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
