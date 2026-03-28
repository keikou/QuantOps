from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
V12_APP = REPO_ROOT / "apps" / "v12-api"
if str(V12_APP) not in sys.path:
    sys.path.insert(0, str(V12_APP))

from ai_hedge_bot.app.container import CONTAINER  # noqa: E402
from ai_hedge_bot.core.enums import Mode  # noqa: E402
from ai_hedge_bot.services.live_trading_service import LiveTradingService  # noqa: E402


def _reset_state() -> None:
    for table in [
        "runtime_control_state",
        "audit_logs",
        "runtime_events",
        "live_orders",
        "live_fills",
        "live_account_balances",
        "live_reconciliation_events",
        "live_incidents",
    ]:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def _capture_artifacts(live_order_id: str) -> dict[str, Any]:
    reconciliation_rows = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT event_type, status, matched
        FROM live_reconciliation_events
        WHERE live_order_id = ?
        ORDER BY created_at ASC
        """,
        [live_order_id],
    )
    incident_rows = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT category, severity, status, summary
        FROM live_incidents
        ORDER BY created_at ASC
        """
    )
    audit_rows = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT category, event_type, actor
        FROM audit_logs
        WHERE category = 'runtime'
        ORDER BY created_at ASC
        """
    )
    order_row = CONTAINER.runtime_store.fetchone_dict(
        "SELECT status FROM live_orders WHERE live_order_id = ?",
        [live_order_id],
    )
    service = LiveTradingService()
    return {
        "reconciliation_rows": reconciliation_rows,
        "incident_rows": incident_rows,
        "audit_rows": audit_rows,
        "order_status": None if order_row is None else order_row["status"],
        "trading_state": str(service.runtime_service.get_trading_state()["trading_state"]).lower(),
    }


def _run_flow(replay: bool) -> dict[str, Any]:
    _reset_state()
    service = LiveTradingService()
    service.runtime_service.resume_trading("recovery replay confidence reset", actor="script")

    submitted = service.submit_live_order(
        symbol="BNBUSDT",
        side="buy",
        qty=2.0,
        urgency="high",
        target_weight=0.28,
        approved=True,
        mode=Mode.LIVE,
    )
    if submitted["status"] != "ok":
        raise RuntimeError(f"submit_live_order failed: {submitted}")

    reconcile_fn = service.replay_live_fill if replay else service.reconcile_live_fill
    result = reconcile_fn(
        live_order_id=submitted["live_order_id"],
        venue_order_id=submitted["venue_order_id"],
        symbol="BNBUSDT",
        side="buy",
        fill_qty=1.0,
        fill_price=610.0,
        free_balance=6400.0,
        locked_balance=1500.0,
        matched=False,
    )
    if result["status"] != "incident":
        raise RuntimeError(f"unexpected reconciliation status: {result}")

    recovered = service.recover_live_incident(
        live_order_id=submitted["live_order_id"],
        venue_order_id=submitted["venue_order_id"],
        resolution_note="verify_recovery_replay_confidence",
        actor="script",
    )
    if recovered["status"] != "ok":
        raise RuntimeError(f"recover_live_incident failed: {recovered}")

    resumed = service.evaluate_live_intent(
        symbol="BNBUSDT",
        urgency="high",
        target_weight=0.28,
        approved=True,
        mode=Mode.LIVE,
    )
    if resumed["status"] != "ok":
        raise RuntimeError(f"evaluate_live_intent after recovery failed: {resumed}")

    return _capture_artifacts(submitted["live_order_id"])


def verify() -> dict[str, Any]:
    failures: list[str] = []
    ingest_artifacts = _run_flow(replay=False)
    replay_artifacts = _run_flow(replay=True)

    if ingest_artifacts["reconciliation_rows"] != replay_artifacts["reconciliation_rows"]:
        failures.append("reconciliation_rows differ between ingest and replay paths")
    if ingest_artifacts["incident_rows"] != replay_artifacts["incident_rows"]:
        failures.append("incident_rows differ between ingest and replay paths")
    if ingest_artifacts["audit_rows"] != replay_artifacts["audit_rows"]:
        failures.append("audit_rows differ between ingest and replay paths")
    if ingest_artifacts["order_status"] != replay_artifacts["order_status"]:
        failures.append("order_status differs between ingest and replay paths")
    if ingest_artifacts["trading_state"] != replay_artifacts["trading_state"]:
        failures.append("trading_state differs between ingest and replay paths")
    if ingest_artifacts["order_status"] != "mismatch":
        failures.append("expected final live order status to remain mismatch after recovery")
    if ingest_artifacts["trading_state"] != "running":
        failures.append("expected trading_state to return to running after recovery")

    return {
        "status": "ok" if not failures else "failed",
        "lane": "recovery_replay_confidence",
        "ingest_artifacts": ingest_artifacts,
        "replay_artifacts": replay_artifacts,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify recovery/replay confidence via equivalent ingest and replay paths.")
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
            "states "
            f"ingest_order={result['ingest_artifacts']['order_status']} "
            f"replay_order={result['replay_artifacts']['order_status']} "
            f"ingest_trading={result['ingest_artifacts']['trading_state']} "
            f"replay_trading={result['replay_artifacts']['trading_state']}"
        )
        if result["failures"]:
            print("failures:")
            for failure in result["failures"]:
                print(f"- {failure}")

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
