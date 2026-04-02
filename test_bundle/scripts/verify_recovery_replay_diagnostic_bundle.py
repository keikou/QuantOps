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

from fastapi.testclient import TestClient  # noqa: E402

from ai_hedge_bot.app.container import CONTAINER  # noqa: E402
from ai_hedge_bot.core.enums import Mode  # noqa: E402
from ai_hedge_bot.services.live_trading_service import LiveTradingService  # noqa: E402


client = TestClient(__import__("ai_hedge_bot.app.main", fromlist=["app"]).app)


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


def _normalized_parity(bundle: dict[str, Any]) -> dict[str, Any]:
    summary = dict(bundle.get("parity_summary") or {})
    summary.pop("source_path", None)
    return summary


def _run_flow(replay: bool) -> dict[str, Any]:
    _reset_state()
    service = LiveTradingService()
    service.runtime_service.resume_trading("recovery replay diagnostic bundle reset", actor="script")

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
        resolution_note="verify_recovery_replay_diagnostic_bundle",
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

    response = client.get("/system/recovery-replay-diagnostic-bundle")
    if response.status_code != 200:
        raise RuntimeError(f"/system/recovery-replay-diagnostic-bundle failed: {response.status_code} {response.text}")
    return response.json()


def verify() -> dict[str, Any]:
    failures: list[str] = []
    ingest_bundle = _run_flow(replay=False)
    replay_bundle = _run_flow(replay=True)

    if ingest_bundle.get("status") != "ok":
        failures.append("ingest bundle did not return status ok")
    if replay_bundle.get("status") != "ok":
        failures.append("replay bundle did not return status ok")

    if str((ingest_bundle.get("parity_summary") or {}).get("source_path")) != "ingest":
        failures.append("ingest bundle source_path should be ingest")
    if str((replay_bundle.get("parity_summary") or {}).get("source_path")) != "replay":
        failures.append("replay bundle source_path should be replay")

    if _normalized_parity(ingest_bundle) != _normalized_parity(replay_bundle):
        failures.append("ingest and replay parity summaries differ beyond source_path")
    if (ingest_bundle.get("consistency") or {}).get("operator_ready") is not True:
        failures.append("ingest bundle consistency operator_ready should be true")
    if (replay_bundle.get("consistency") or {}).get("operator_ready") is not True:
        failures.append("replay bundle consistency operator_ready should be true")
    if list((ingest_bundle.get("consistency") or {}).get("mismatches") or []):
        failures.append("ingest bundle mismatches should be empty")
    if list((replay_bundle.get("consistency") or {}).get("mismatches") or []):
        failures.append("replay bundle mismatches should be empty")

    ingest_events = [str(item.get("event_type") or "") for item in ingest_bundle.get("reconciliation_events") or []]
    replay_events = [str(item.get("event_type") or "") for item in replay_bundle.get("reconciliation_events") or []]
    if ingest_events != replay_events:
        failures.append("ingest and replay reconciliation event type chains differ")
    if ingest_events != ["order_submitted", "fill_mismatch", "recovery_resolved"]:
        failures.append("unexpected reconciliation event chain in recovery/replay bundle")

    if str((ingest_bundle.get("incident") or {}).get("status")) != "resolved":
        failures.append("ingest bundle incident status should be resolved")
    if str((replay_bundle.get("incident") or {}).get("status")) != "resolved":
        failures.append("replay bundle incident status should be resolved")
    if str((ingest_bundle.get("recovery_summary") or {}).get("trading_state")) != "running":
        failures.append("ingest bundle trading_state should be running after recovery")
    if str((replay_bundle.get("recovery_summary") or {}).get("trading_state")) != "running":
        failures.append("replay bundle trading_state should be running after recovery")
    if str((ingest_bundle.get("order") or {}).get("status")) != "mismatch":
        failures.append("ingest bundle final order status should remain mismatch")
    if str((replay_bundle.get("order") or {}).get("status")) != "mismatch":
        failures.append("replay bundle final order status should remain mismatch")

    return {
        "status": "ok" if not failures else "failed",
        "lane": "recovery_replay_diagnostic_bundle",
        "ingest_bundle": {
            "live_order_id": ingest_bundle.get("live_order_id"),
            "parity_summary": ingest_bundle.get("parity_summary"),
            "consistency": ingest_bundle.get("consistency"),
        },
        "replay_bundle": {
            "live_order_id": replay_bundle.get("live_order_id"),
            "parity_summary": replay_bundle.get("parity_summary"),
            "consistency": replay_bundle.get("consistency"),
        },
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the recovery/replay diagnostic bundle preserves parity across ingest and replay live mismatch flows.")
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
            "paths "
            f"ingest={(result['ingest_bundle'].get('parity_summary') or {}).get('source_path')} "
            f"replay={(result['replay_bundle'].get('parity_summary') or {}).get('source_path')}"
        )
        if result["failures"]:
            print("failures:")
            for failure in result["failures"]:
                print(f"- {failure}")

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
