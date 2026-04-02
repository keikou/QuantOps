from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.repositories.sprint5_repository import Sprint5Repository
from ai_hedge_bot.services.execution_bridge_diagnostics_service import ExecutionBridgeDiagnosticsService
from ai_hedge_bot.services.runtime.runtime_service import RuntimeService


class OperatorDiagnosticBundleService:
    def __init__(self) -> None:
        self.runtime_service = RuntimeService()
        self.bridge_service = ExecutionBridgeDiagnosticsService()
        self.repo = Sprint5Repository()
        self.store = CONTAINER.runtime_store

    @staticmethod
    def _decode(raw: object) -> dict[str, Any]:
        if isinstance(raw, dict):
            return dict(raw)
        try:
            return json.loads(str(raw or "{}"))
        except Exception:
            return {}

    @staticmethod
    def _snapshot_age_sec(value: object) -> float | None:
        if value in (None, ""):
            return None
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return round(max(0.0, (datetime.now(timezone.utc) - dt).total_seconds()), 3)
        except Exception:
            return None

    def _latest_checkpoint_payload(self, run_id: str | None) -> dict[str, Any]:
        if run_id:
            row = self.store.fetchone_dict(
                """
                SELECT run_id, created_at, payload_json
                FROM runtime_checkpoints
                WHERE checkpoint_name = 'latest_orchestrator_run' AND run_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                [run_id],
            )
            if row:
                payload = self._decode(row.get("payload_json"))
                payload.setdefault("run_id", row.get("run_id"))
                payload.setdefault("checkpoint_created_at", row.get("created_at"))
                return payload

        row = self.store.fetchone_dict(
            """
            SELECT run_id, created_at, payload_json
            FROM runtime_checkpoints
            WHERE checkpoint_name = 'latest_orchestrator_run'
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        if not row:
            return {}
        payload = self._decode(row.get("payload_json"))
        payload.setdefault("run_id", row.get("run_id"))
        payload.setdefault("checkpoint_created_at", row.get("created_at"))
        return payload

    def _latest_portfolio_diagnostics(self) -> dict[str, Any]:
        if CONTAINER.latest_portfolio_diagnostics:
            return {
                "status": "ok",
                "diagnostics": dict(CONTAINER.latest_portfolio_diagnostics),
                "as_of": utc_now_iso_fallback(),
            }
        row = self.store.fetchone_dict(
            """
            SELECT created_at, input_signals, kept_signals, crowding_flags_json, overlap_penalty_applied
            FROM portfolio_diagnostics
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        if not row:
            return {"status": "ok", "diagnostics": {}, "as_of": None}
        return {
            "status": "ok",
            "diagnostics": {
                "input_signals": int(row.get("input_signals", 0) or 0),
                "kept_signals": int(row.get("kept_signals", 0) or 0),
                "crowding_flags": self._decode(row.get("crowding_flags_json")),
                "overlap_penalty_applied": bool(row.get("overlap_penalty_applied", False)),
            },
            "as_of": row.get("created_at"),
        }

    def build(self) -> dict[str, Any]:
        checkpoint = self._latest_checkpoint_payload(run_id=None)
        run_id = str(checkpoint.get("run_id") or "") or None
        bridge = self.bridge_service.get_bridge_summary(run_id=run_id)
        run_id = str(bridge.get("run_id") or run_id or "") or None
        runtime_run = self.runtime_service.get_run(run_id) if run_id else None
        execution_quality = self.repo.latest_execution_quality_summary()
        portfolio_overview = self.repo.latest_portfolio_overview_summary()
        signal_snapshot = self.repo.latest_signal_snapshot()
        portfolio_diagnostics = self._latest_portfolio_diagnostics()
        orchestrator_run = checkpoint or dict(CONTAINER.latest_orchestrator_run or {})

        details = dict(orchestrator_run.get("details") or {})
        runtime_governance_linkage = details.get("runtime_governance_linkage") or {}
        config_provenance = orchestrator_run.get("config_provenance") or {}
        deploy_provenance = orchestrator_run.get("deploy_provenance") or {}
        bridge_state = str(bridge.get("bridge_state") or "")

        mismatches: list[str] = []

        def _check_match(label: str, actual: object) -> None:
            actual_value = str(actual or "") or None
            if run_id and actual_value and actual_value != run_id:
                mismatches.append(f"{label}_run_id_mismatch")

        _check_match("execution_quality", execution_quality.get("run_id"))
        if bridge_state != "no_decision":
            _check_match("portfolio_overview", (portfolio_overview.get("snapshot") or {}).get("run_id"))
        _check_match("signal_snapshot", (signal_snapshot.get("snapshot") or {}).get("run_id"))
        _check_match("runtime_run", (runtime_run or {}).get("run_id"))
        if run_id and str(orchestrator_run.get("run_id") or "") not in {"", run_id}:
            mismatches.append("orchestrator_run_id_mismatch")
        if str(bridge.get("cycle_id") or "") and str(orchestrator_run.get("cycle_id") or "") and str(bridge.get("cycle_id")) != str(orchestrator_run.get("cycle_id")):
            mismatches.append("cycle_id_mismatch")
        if not str(config_provenance.get("fingerprint") or ""):
            mismatches.append("missing_config_provenance")
        if not str(deploy_provenance.get("fingerprint") or ""):
            mismatches.append("missing_deploy_provenance")
        if bridge.get("event_chain_complete") is not True:
            mismatches.append("execution_bridge_incomplete")
        if runtime_governance_linkage and not str(runtime_governance_linkage.get("alpha_id") or ""):
            mismatches.append("governance_linkage_missing_alpha")
        if runtime_governance_linkage and not str(runtime_governance_linkage.get("model_id") or ""):
            mismatches.append("governance_linkage_missing_model")

        source_snapshot_time = (
            orchestrator_run.get("timestamp")
            or orchestrator_run.get("checkpoint_created_at")
            or (runtime_run or {}).get("finished_at")
            or bridge.get("last_transition_at")
            or (execution_quality or {}).get("as_of")
            or (portfolio_overview.get("summary") or {}).get("source_snapshot_time")
        )

        consistency = {
            "status": "ok" if not mismatches else "warn",
            "run_id": run_id,
            "cycle_id": bridge.get("cycle_id") or orchestrator_run.get("cycle_id"),
            "bridge_state": bridge_state,
            "run_status": (runtime_run or {}).get("status"),
            "config_fingerprint": config_provenance.get("fingerprint"),
            "deploy_fingerprint": deploy_provenance.get("fingerprint"),
            "governance_linked": bool(runtime_governance_linkage),
            "operator_ready": not mismatches,
            "mismatches": mismatches,
        }

        return {
            "status": "ok",
            "run_id": run_id,
            "cycle_id": consistency["cycle_id"],
            "mode": orchestrator_run.get("mode") or (runtime_run or {}).get("mode"),
            "source_snapshot_time": source_snapshot_time,
            "data_freshness_sec": self._snapshot_age_sec(source_snapshot_time),
            "operator_summary": {
                "trading_state": self.runtime_service.get_trading_state().get("trading_state", "running"),
                "bridge_state": bridge_state,
                "cycle_status": bridge.get("cycle_status"),
                "operator_message": bridge.get("operator_message"),
                "event_chain_complete": bool(bridge.get("event_chain_complete", False)),
                "planned_count": int(bridge.get("planned_count", 0) or 0),
                "submitted_count": int(bridge.get("submitted_count", 0) or 0),
                "filled_count": int(bridge.get("filled_count", 0) or 0),
            },
            "runtime_run": runtime_run or {"status": "missing"},
            "execution_bridge": bridge,
            "execution_quality": execution_quality,
            "portfolio_overview": portfolio_overview,
            "portfolio_diagnostics": portfolio_diagnostics,
            "signal_snapshot": signal_snapshot,
            "latest_orchestrator_run": orchestrator_run,
            "runtime_governance_linkage": runtime_governance_linkage,
            "config_provenance": config_provenance,
            "deploy_provenance": deploy_provenance,
            "consistency": consistency,
        }


def utc_now_iso_fallback() -> str:
    return datetime.now(timezone.utc).isoformat()
