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
from ai_hedge_bot.app.main import app  # noqa: E402
from ai_hedge_bot.core.settings import SETTINGS  # noqa: E402


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
]


def _reset_state() -> None:
    for table in RESET_TABLES:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def _decode_payload(raw: str | None) -> dict[str, Any]:
    try:
        return json.loads(str(raw or "{}"))
    except Exception:
        return {}


def verify() -> dict[str, Any]:
    failures: list[str] = []

    _reset_state()
    response = client.post("/runtime/run-once")
    if response.status_code != 200:
        raise RuntimeError(f"/runtime/run-once failed: {response.status_code} {response.text}")
    body = response.json()
    run_id = body["run_id"]

    run_started_row = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT payload_json, actor
        FROM audit_logs
        WHERE run_id = ? AND event_type = 'run_started'
        ORDER BY created_at ASC
        LIMIT 1
        """,
        [run_id],
    )
    checkpoint_row = CONTAINER.runtime_store.fetchone_dict(
        """
        SELECT checkpoint_name, payload_json
        FROM runtime_checkpoints
        WHERE run_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [run_id],
    )

    run_started_payload = _decode_payload((run_started_row or {}).get("payload_json"))
    checkpoint_payload = _decode_payload((checkpoint_row or {}).get("payload_json"))
    response_provenance = body.get("config_provenance") or {}
    run_started_provenance = run_started_payload.get("config_provenance") or {}
    checkpoint_provenance = checkpoint_payload.get("config_provenance") or {}

    response_fingerprint = str(response_provenance.get("fingerprint") or "")
    run_started_fingerprint = str(run_started_provenance.get("fingerprint") or "")
    checkpoint_fingerprint = str(checkpoint_provenance.get("fingerprint") or "")

    if body.get("status") != "ok":
        failures.append("runtime run did not complete successfully")
    if not response_fingerprint:
        failures.append("runtime API response missing config_provenance fingerprint")
    if not run_started_fingerprint:
        failures.append("run_started audit payload missing config_provenance fingerprint")
    if not checkpoint_fingerprint:
        failures.append("runtime checkpoint payload missing config_provenance fingerprint")
    if len({response_fingerprint, run_started_fingerprint, checkpoint_fingerprint}) != 1:
        failures.append("config_provenance fingerprint differs across response, run_started audit, and checkpoint")

    run_snapshot = run_started_provenance.get("snapshot") or {}
    checkpoint_snapshot = checkpoint_provenance.get("snapshot") or {}
    if str((run_snapshot.get("app_config") or {}).get("mode")) != "paper":
        failures.append("run_started config snapshot missing expected app_config.mode")
    if str((run_snapshot.get("settings") or {}).get("timeframe")) != SETTINGS.timeframe:
        failures.append("run_started config snapshot missing expected settings.timeframe")
    if list((run_snapshot.get("app_config") or {}).get("symbols") or []) != list(CONTAINER.config.symbols):
        failures.append("run_started config snapshot missing expected app_config.symbols")
    if str((run_snapshot.get("mode_policy") or {}).get("mode")) != "paper":
        failures.append("run_started config snapshot missing expected mode_policy.mode")
    if str((run_snapshot.get("truth_price_runtime") or {}).get("price_source")) != SETTINGS.price_source:
        failures.append("run_started config snapshot missing expected truth_price_runtime.price_source")
    if str((checkpoint_snapshot.get("mode_policy") or {}).get("mode")) != "paper":
        failures.append("checkpoint config snapshot missing expected mode_policy.mode")

    if str((checkpoint_row or {}).get("checkpoint_name")) != "latest_orchestrator_run":
        failures.append("expected latest runtime checkpoint to be latest_orchestrator_run")
    if str((checkpoint_payload or {}).get("run_id")) != run_id:
        failures.append("checkpoint payload missing expected run_id")

    return {
        "status": "ok" if not failures else "failed",
        "lane": "runtime_config_provenance",
        "run_id": run_id,
        "response_provenance": response_provenance,
        "run_started_provenance": run_started_provenance,
        "checkpoint_provenance": checkpoint_provenance,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify runtime config provenance is persisted to audit and checkpoint surfaces.")
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
        print(f"fingerprint={result['response_provenance'].get('fingerprint')}")
        if result["failures"]:
            print("failures:")
            for failure in result["failures"]:
                print(f"- {failure}")

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
