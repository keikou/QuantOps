from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
V12_APP = REPO_ROOT / "apps" / "v12-api"
if str(V12_APP) not in sys.path:
    sys.path.insert(0, str(V12_APP))

from fastapi.testclient import TestClient  # noqa: E402

from ai_hedge_bot.app.container import CONTAINER  # noqa: E402
from ai_hedge_bot.app.main import app  # noqa: E402
from ai_hedge_bot.core.enums import Mode  # noqa: E402
from ai_hedge_bot.services.live_trading_service import LiveTradingService  # noqa: E402
from ai_hedge_bot.services.self_improving_service import SelfImprovingService  # noqa: E402
from ai_hedge_bot.signal import signal_service as signal_service_module  # noqa: E402


client = TestClient(app)


RESET_TABLES = [
    "runtime_control_state",
    "runtime_runs",
    "runtime_run_steps",
    "scheduler_runs",
    "runtime_checkpoints",
    "runtime_events",
    "audit_logs",
    "signals",
    "signal_evaluations",
    "alpha_signal_snapshots",
    "alpha_candidates",
    "portfolio_signal_decisions",
    "portfolio_diagnostics",
    "portfolio_snapshots",
    "portfolio_positions",
    "rebalance_plans",
    "execution_plans",
    "execution_orders",
    "execution_fills",
    "execution_quality_snapshots",
    "execution_state_snapshots",
    "execution_block_reasons",
    "shadow_orders",
    "shadow_fills",
    "shadow_pnl_snapshots",
    "orchestrator_runs",
    "orchestrator_cycles",
    "market_prices_latest",
    "market_prices_history",
    "position_snapshots_latest",
    "position_snapshots_history",
    "position_snapshot_versions",
    "equity_snapshots",
    "cash_ledger",
    "truth_engine_state",
    "experiment_tracker",
    "validation_registry",
    "model_registry",
    "model_state_transitions",
    "model_live_reviews",
    "alpha_registry",
    "alpha_status_events",
    "alpha_library",
    "alpha_promotions",
    "alpha_demotions",
    "alpha_rankings",
    "live_orders",
    "live_fills",
    "live_account_balances",
    "live_reconciliation_events",
    "live_incidents",
]


class _FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        fixed = datetime(2026, 3, 29, 14, 15, tzinfo=timezone.utc)
        if tz is None:
            return fixed.replace(tzinfo=None)
        return fixed.astimezone(tz)


def _reset_state() -> None:
    for table in RESET_TABLES:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def _register_model(alpha_id: str, model_id: str) -> None:
    endpoints = [
        (
            "/alpha/generate",
            {
                "alpha_id": alpha_id,
                "alpha_family": "derivatives",
                "factor_type": "carry",
                "feature_dependencies": ["funding_rate", "oi_delta"],
            },
        ),
        (
            "/research-factory/experiments/register",
            {
                "experiment_id": f"exp_{alpha_id}",
                "dataset_version": "dataset.phase7.v1",
                "feature_version": "features.phase7.v1",
                "model_version": "model.phase7.v1",
                "alpha_id": alpha_id,
                "strategy_id": "trend_core",
            },
        ),
        (
            "/research-factory/validations/register",
            {
                "experiment_id": f"exp_{alpha_id}",
                "summary_score": 0.84,
                "passed": True,
            },
        ),
        (
            "/research-factory/models/register",
            {
                "model_id": model_id,
                "experiment_id": f"exp_{alpha_id}",
                "dataset_version": "dataset.phase7.v1",
                "feature_version": "features.phase7.v1",
                "model_version": "model.phase7.v1",
                "validation_metrics": {"summary_score": 0.84, "max_drawdown": 0.06},
                "state": "live",
            },
        ),
    ]
    for path, payload in endpoints:
        response = client.post(path, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"{path} failed: {response.status_code} {response.text}")


def _signal_map(created_at: str) -> dict[str, dict[str, Any]]:
    rows = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT symbol, score, dominant_alpha
        FROM signals
        WHERE created_at = ?
        ORDER BY symbol ASC
        """,
        [created_at],
    )
    return {str(row["symbol"]): row for row in rows}


def _decision_map(created_at: str) -> dict[str, float]:
    rows = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT symbol, target_weight
        FROM portfolio_signal_decisions
        WHERE created_at = ?
        ORDER BY symbol ASC
        """,
        [created_at],
    )
    return {str(row["symbol"]): abs(float(row["target_weight"] or 0.0)) for row in rows}


def _truth_artifacts() -> dict[str, Any]:
    truth_state = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT state_key, state_value
        FROM truth_engine_state
        ORDER BY state_key ASC
        """
    )
    price_count = CONTAINER.runtime_store.fetchone_dict("SELECT COUNT(*) AS c FROM market_prices_latest")
    position_count = CONTAINER.runtime_store.fetchone_dict("SELECT COUNT(*) AS c FROM position_snapshots_latest")
    equity_count = CONTAINER.runtime_store.fetchone_dict("SELECT COUNT(*) AS c FROM equity_snapshots")
    latest_equity = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT total_equity, gross_exposure, net_exposure
        FROM equity_snapshots
        ORDER BY snapshot_time DESC
        LIMIT 1
        """
    )
    return {
        "truth_state": truth_state,
        "market_price_count": int((price_count or {}).get("c", 0) or 0),
        "position_snapshot_count": int((position_count or {}).get("c", 0) or 0),
        "equity_snapshot_count": int((equity_count or {}).get("c", 0) or 0),
        "latest_equity": latest_equity,
    }


def _bridge_artifacts(run_id: str) -> dict[str, Any]:
    response = client.get(f"/execution/bridge/by-run/{run_id}")
    if response.status_code != 200:
        raise RuntimeError(f"/execution/bridge/by-run/{run_id} failed: {response.status_code}")
    return response.json()


def _self_improving_artifacts(model_id: str, alpha_id: str) -> dict[str, Any]:
    latest_review = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT decision, notes
        FROM model_live_reviews
        WHERE model_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [model_id],
    )
    latest_transition = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT from_state, to_state, reason
        FROM model_state_transitions
        WHERE model_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [model_id],
    )
    latest_alpha = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT state
        FROM alpha_library
        WHERE alpha_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [alpha_id],
    )
    latest_alpha_event = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT event_type, to_state, reason
        FROM alpha_status_events
        WHERE alpha_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [alpha_id],
    )
    latest_promotion = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT decision, source_run_id
        FROM alpha_promotions
        WHERE alpha_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [alpha_id],
    )
    return {
        "latest_review": latest_review,
        "latest_transition": latest_transition,
        "latest_alpha": latest_alpha,
        "latest_alpha_event": latest_alpha_event,
        "latest_promotion": latest_promotion,
    }


def _run_live_acceptance(target_weight: float) -> dict[str, Any]:
    service = LiveTradingService()
    halted = service.runtime_service.halt_trading("cross phase acceptance halt", actor="script")
    blocked = service.evaluate_live_intent(
        symbol="BTCUSDT",
        urgency="high",
        target_weight=target_weight,
        approved=True,
        mode=Mode.LIVE,
    )
    resumed = service.runtime_service.resume_trading("cross phase acceptance resume", actor="script")
    submitted = service.submit_live_order(
        symbol="BTCUSDT",
        side="buy",
        qty=max(round(target_weight, 4), 0.1),
        urgency="high",
        target_weight=target_weight,
        approved=True,
        mode=Mode.LIVE,
    )
    if submitted["status"] != "ok":
        raise RuntimeError(f"submit_live_order failed: {submitted}")
    reconciled = service.reconcile_live_fill(
        live_order_id=submitted["live_order_id"],
        venue_order_id=submitted["venue_order_id"],
        symbol="BTCUSDT",
        side="buy",
        fill_qty=max(round(target_weight, 4), 0.1),
        fill_price=100000.0,
        free_balance=9000.0,
        locked_balance=1000.0,
        matched=True,
    )
    live_order = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT status, venue, order_type, tif
        FROM live_orders
        WHERE live_order_id = ?
        """,
        [submitted["live_order_id"]],
    )
    live_events = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT event_type, status, matched
        FROM live_reconciliation_events
        WHERE live_order_id = ?
        ORDER BY created_at ASC
        """,
        [submitted["live_order_id"]],
    )
    incident_count = CONTAINER.runtime_store.fetchone_dict("SELECT COUNT(*) AS c FROM live_incidents")
    return {
        "halted": halted,
        "blocked": blocked,
        "resumed": resumed,
        "submitted": submitted,
        "reconciled": reconciled,
        "live_order": live_order,
        "live_events": live_events,
        "incident_count": int((incident_count or {}).get("c", 0) or 0),
    }


def verify() -> dict[str, Any]:
    failures: list[str] = []
    alpha_id = "alpha.cross.phase.acceptance"
    model_id = "model_cross_phase_acceptance"

    _reset_state()
    _register_model(alpha_id, model_id)

    resume = client.post("/runtime/resume")
    if resume.status_code != 200:
        raise RuntimeError(f"/runtime/resume failed: {resume.status_code}")

    original_datetime = signal_service_module.datetime
    signal_service_module.datetime = _FixedDateTime
    try:
        baseline_response = client.post("/runtime/run-once?mode=paper")
        if baseline_response.status_code != 200:
            raise RuntimeError(f"baseline /runtime/run-once failed: {baseline_response.status_code}")
        baseline_payload = baseline_response.json()

        self_improving = SelfImprovingService().evaluate_result_evidence(
            {
                "created_at": "2026-03-29T14:20:00+00:00",
                "model_id": model_id,
                "strategy_id": "trend_core",
                "expected_return": 0.12,
                "realized_return": 0.11,
                "hit_rate": 0.68,
                "turnover": 0.32,
                "drawdown": -0.05,
                "slippage_bps": 4.0,
                "fill_rate": 0.91,
                "risk_usage": 0.52,
                "notes": "cross phase acceptance promotion",
            }
        )

        promoted_response = client.post("/runtime/run-once?mode=paper")
        if promoted_response.status_code != 200:
            raise RuntimeError(f"promoted /runtime/run-once failed: {promoted_response.status_code}")
        promoted_payload = promoted_response.json()
    finally:
        signal_service_module.datetime = original_datetime

    baseline_signals = _signal_map(baseline_payload["result"]["timestamp"])
    promoted_signals = _signal_map(promoted_payload["result"]["timestamp"])
    baseline_decisions = _decision_map(baseline_payload["result"]["timestamp"])
    promoted_decisions = _decision_map(promoted_payload["result"]["timestamp"])
    bridge = _bridge_artifacts(promoted_payload["run_id"])
    truth = _truth_artifacts()
    self_improving_artifacts = _self_improving_artifacts(model_id, alpha_id)
    btc_target_weight = promoted_decisions.get("BTCUSDT", 0.0)
    live = _run_live_acceptance(btc_target_weight)

    if baseline_payload.get("status") != "ok":
        failures.append("baseline paper cycle did not complete successfully")
    if promoted_payload.get("status") != "ok":
        failures.append("promoted paper cycle did not complete successfully")
    if self_improving.get("decision") != "keep":
        failures.append("expected self-improving decision to be keep for acceptance scenario")

    baseline_btc = baseline_signals.get("BTCUSDT") or {}
    promoted_btc = promoted_signals.get("BTCUSDT") or {}
    if str(baseline_btc.get("dominant_alpha")) != "phase6_dynamic_alpha":
        failures.append("expected baseline BTC dominant_alpha to remain phase6_dynamic_alpha")
    if str(promoted_btc.get("dominant_alpha")) != alpha_id:
        failures.append("expected promoted BTC dominant_alpha to switch to acceptance alpha")
    if float(promoted_btc.get("score", 0.0) or 0.0) <= float(baseline_btc.get("score", 0.0) or 0.0):
        failures.append("expected promoted BTC score to exceed baseline BTC score")

    if promoted_decisions.get("BTCUSDT", 0.0) <= baseline_decisions.get("BTCUSDT", 0.0):
        failures.append("expected promoted BTC target_weight to exceed baseline target_weight")
    if btc_target_weight <= 0.0:
        failures.append("expected promoted BTC target_weight to remain positive")

    if bridge.get("status") != "ok":
        failures.append("execution bridge did not return ok status")
    if bridge.get("event_chain_complete") is not True:
        failures.append("execution bridge did not report a complete event chain")
    if str(bridge.get("bridge_state")) != "filled":
        failures.append("execution bridge did not reach filled state")
    if int(bridge.get("planned_count", 0) or 0) < 1:
        failures.append("expected at least one execution plan in promoted cycle")
    if int(bridge.get("filled_count", 0) or 0) < 1:
        failures.append("expected at least one execution fill in promoted cycle")

    truth_state_keys = {str(row.get("state_key")) for row in truth["truth_state"]}
    required_truth_keys = {"positions_last_fill", "equity_last_fill", "equity_snapshot_state"}
    if not required_truth_keys.issubset(truth_state_keys):
        failures.append("truth_engine_state is missing required acceptance keys")
    if truth["market_price_count"] < 1:
        failures.append("expected market_prices_latest rows after promoted cycle")
    if truth["position_snapshot_count"] < 1:
        failures.append("expected position_snapshots_latest rows after promoted cycle")
    if truth["equity_snapshot_count"] < 1:
        failures.append("expected equity_snapshots rows after promoted cycle")
    latest_equity = truth["latest_equity"] or {}
    if float(latest_equity.get("total_equity", 0.0) or 0.0) <= 0.0:
        failures.append("expected latest total_equity to be positive")

    latest_review = self_improving_artifacts["latest_review"] or {}
    latest_transition = self_improving_artifacts["latest_transition"] or {}
    latest_alpha = self_improving_artifacts["latest_alpha"] or {}
    latest_alpha_event = self_improving_artifacts["latest_alpha_event"] or {}
    latest_promotion = self_improving_artifacts["latest_promotion"] or {}
    if str(latest_review.get("decision")) != "keep":
        failures.append("expected latest model review decision to remain keep")
    if str(latest_review.get("notes")) != "cross phase acceptance promotion":
        failures.append("expected latest model review note to match acceptance scenario")
    if str(latest_transition.get("to_state")) != "live":
        failures.append("expected model transition to move into live state")
    if str(latest_transition.get("reason")) not in {"self_improving_keep", "initial_registration"}:
        failures.append("expected model transition reason to remain attributable to registration or self_improving_keep")
    if str(latest_alpha.get("state")) != "promoted":
        failures.append("expected promoted alpha to remain in promoted state")
    if str(latest_alpha_event.get("to_state")) != "promoted":
        failures.append("expected latest alpha event to keep promoted state")
    if str(latest_alpha_event.get("reason")) != "self_improving_keep":
        failures.append("expected latest alpha event reason self_improving_keep")
    if str(latest_promotion.get("decision")) != "promote":
        failures.append("expected alpha promotion decision to be promote")
    if str(latest_promotion.get("source_run_id")) != "self_improving_keep":
        failures.append("expected alpha promotion source_run_id to be self_improving_keep")

    if str((live["blocked"] or {}).get("status")) != "blocked":
        failures.append("expected halted guard state to block live intent")
    if str((live["blocked"] or {}).get("reason_code")) != "execution_disabled":
        failures.append("expected halted live intent reason_code execution_disabled")
    if str((live["resumed"] or {}).get("trading_state")) != "running":
        failures.append("expected runtime resume to restore running state before live send")
    if str((live["submitted"] or {}).get("status")) != "ok":
        failures.append("expected resumed live submit to succeed")
    if str((live["submitted"] or {}).get("decision")) != "live_send":
        failures.append("expected resumed live submit decision to be live_send")
    if str((live["reconciled"] or {}).get("status")) != "ok":
        failures.append("expected matched live reconciliation to succeed")
    if str((live["reconciled"] or {}).get("order_status")) != "filled":
        failures.append("expected matched live reconciliation to fill the order")

    live_order = live["live_order"] or {}
    if str(live_order.get("status")) != "filled":
        failures.append("expected persisted live order status to be filled")
    if str(live_order.get("venue")) != "binance_live":
        failures.append("expected persisted live order venue to be binance_live")
    if str(live_order.get("order_type")) != "market":
        failures.append("expected persisted live order type to be market")
    if str(live_order.get("tif")) != "IOC":
        failures.append("expected persisted live order tif to be IOC")
    if [str(row.get("event_type")) for row in live["live_events"]] != ["order_submitted", "fill_reconciled"]:
        failures.append("expected live reconciliation event chain order_submitted -> fill_reconciled")
    if live["incident_count"] != 0:
        failures.append("expected no live incidents in matched acceptance path")

    return {
        "status": "ok" if not failures else "failed",
        "lane": "cross_phase_acceptance",
        "baseline": {
            "run_id": baseline_payload["run_id"],
            "timestamp": baseline_payload["result"]["timestamp"],
            "btc_signal": baseline_btc,
            "btc_target_weight": baseline_decisions.get("BTCUSDT", 0.0),
        },
        "promoted": {
            "run_id": promoted_payload["run_id"],
            "timestamp": promoted_payload["result"]["timestamp"],
            "btc_signal": promoted_btc,
            "btc_target_weight": btc_target_weight,
        },
        "self_improving": {
            "result": self_improving,
            "artifacts": self_improving_artifacts,
        },
        "bridge": bridge,
        "truth": truth,
        "live": live,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify cross-phase acceptance through runtime, governance, guard, and live evidence.")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    try:
        result = verify()
    except Exception as exc:
        print(f"Verification failed unexpectedly: {exc}", file=sys.stderr)
        return 3

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status={result['status']} lane={result['lane']}")
        print(
            "btc "
            f"baseline_alpha={result['baseline']['btc_signal'].get('dominant_alpha')} "
            f"promoted_alpha={result['promoted']['btc_signal'].get('dominant_alpha')} "
            f"baseline_weight={result['baseline']['btc_target_weight']:.6f} "
            f"promoted_weight={result['promoted']['btc_target_weight']:.6f}"
        )
        print(
            "live "
            f"blocked_reason={result['live']['blocked'].get('reason_code')} "
            f"submit_decision={result['live']['submitted'].get('decision')} "
            f"reconcile_status={result['live']['reconciled'].get('status')}"
        )
        if result["failures"]:
            print("failures:")
            for failure in result["failures"]:
                print(f"- {failure}")

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
