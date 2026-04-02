from __future__ import annotations

import json
from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.services.operator_diagnostic_bundle_service import OperatorDiagnosticBundleService
from ai_hedge_bot.services.recovery_replay_diagnostic_bundle_service import RecoveryReplayDiagnosticBundleService


class HardeningStatusService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.operator_bundle = OperatorDiagnosticBundleService()
        self.recovery_bundle = RecoveryReplayDiagnosticBundleService()

    @staticmethod
    def _decode(raw: object) -> dict[str, Any]:
        if isinstance(raw, dict):
            return dict(raw)
        try:
            return json.loads(str(raw or "{}"))
        except Exception:
            return {}

    def _research_event_counts(self) -> dict[str, int]:
        rows = self.store.fetchall_dict(
            """
            SELECT event_type, COUNT(*) AS cnt
            FROM audit_logs
            WHERE category = 'research_factory'
            GROUP BY event_type
            """
        )
        return {str(row.get("event_type") or ""): int(row.get("cnt", 0) or 0) for row in rows}

    def _runtime_audit_chain(self, run_id: str | None) -> list[str]:
        if not run_id:
            return []
        rows = self.store.fetchall_dict(
            """
            SELECT event_type
            FROM audit_logs
            WHERE category = 'runtime' AND run_id = ?
            ORDER BY created_at ASC
            """,
            [run_id],
        )
        return [str(row.get("event_type") or "") for row in rows]

    def _multi_cycle_linkage_ready(self, alpha_id: str | None, model_id: str | None) -> bool:
        if not alpha_id or not model_id:
            return False
        rows = self.store.fetchall_dict(
            """
            SELECT payload_json
            FROM runtime_checkpoints
            WHERE checkpoint_name = 'latest_orchestrator_run'
            ORDER BY created_at DESC
            LIMIT 10
            """
        )
        matched = 0
        for row in rows:
            payload = self._decode(row.get("payload_json"))
            linkage = ((payload.get("details") or {}).get("runtime_governance_linkage") or {})
            if str(linkage.get("alpha_id") or "") == alpha_id and str(linkage.get("model_id") or "") == model_id:
                matched += 1
        return matched >= 2

    def build(self) -> dict[str, Any]:
        operator_bundle = self.operator_bundle.build()
        recovery_bundle = self.recovery_bundle.build()
        run_id = str(operator_bundle.get("run_id") or "") or None
        linkage = operator_bundle.get("runtime_governance_linkage") or {}
        consistency = operator_bundle.get("consistency") or {}
        recovery_consistency = recovery_bundle.get("consistency") or {}
        research_counts = self._research_event_counts()
        runtime_audit_chain = self._runtime_audit_chain(run_id)

        config_fp = str((operator_bundle.get("config_provenance") or {}).get("fingerprint") or "")
        deploy_fp = str((operator_bundle.get("deploy_provenance") or {}).get("fingerprint") or "")
        alpha_id = str(linkage.get("alpha_id") or "") or None
        model_id = str(linkage.get("model_id") or "") or None

        packets = [
            {
                "packet": "recovery_replay_confidence",
                "ready": bool(recovery_bundle.get("status") == "ok" and recovery_consistency.get("operator_ready") is True),
                "summary": "latest recovery/replay bundle is operator-ready",
            },
            {
                "packet": "cross_phase_acceptance",
                "ready": bool(consistency.get("operator_ready") is True and alpha_id and model_id),
                "summary": "latest accepted cycle is attributable across runtime, bridge, and portfolio surfaces",
            },
            {
                "packet": "audit_provenance_gap_review",
                "ready": bool(run_id and runtime_audit_chain == ["run_started", "checkpoint_created", "run_finished"] and config_fp and deploy_fp),
                "summary": "runtime audit chain and checkpoint provenance are coherent",
            },
            {
                "packet": "research_audit_mirroring",
                "ready": all(research_counts.get(name, 0) > 0 for name in [
                    "dataset_registered",
                    "feature_registered",
                    "experiment_registered",
                    "validation_registered",
                    "model_registered",
                ]),
                "summary": "research registrations are mirrored into the unified audit stream",
            },
            {
                "packet": "research_governance_audit_mirroring",
                "ready": any(research_counts.get(name, 0) > 0 for name in [
                    "promotion_evaluated",
                    "live_review_evaluated",
                    "alpha_decay_evaluated",
                    "rollback_evaluated",
                    "champion_challenger_run",
                ]),
                "summary": "research governance decisions are mirrored into the unified audit stream",
            },
            {
                "packet": "runtime_config_provenance",
                "ready": bool(config_fp),
                "summary": "latest accepted run carries an effective config fingerprint",
            },
            {
                "packet": "deploy_provenance",
                "ready": bool(deploy_fp),
                "summary": "latest accepted run carries a deploy fingerprint",
            },
            {
                "packet": "runtime_governance_linkage",
                "ready": bool(alpha_id and model_id and str(linkage.get("decision_source") or "")),
                "summary": "latest accepted run carries explicit governance linkage",
            },
            {
                "packet": "multi_cycle_acceptance",
                "ready": self._multi_cycle_linkage_ready(alpha_id=alpha_id, model_id=model_id),
                "summary": "more than one accepted cycle preserves the same governance linkage",
            },
            {
                "packet": "operator_diagnostic_bundle",
                "ready": bool(operator_bundle.get("status") == "ok" and consistency.get("operator_ready") is True),
                "summary": "latest accepted runtime cycle is visible in one operator bundle",
            },
            {
                "packet": "recovery_replay_diagnostic_bundle",
                "ready": bool(recovery_bundle.get("status") == "ok" and recovery_consistency.get("operator_ready") is True),
                "summary": "latest recovery/replay chain is visible in one operator bundle",
            },
        ]

        overall_ready = all(bool(item["ready"]) for item in packets)
        return {
            "status": "ok",
            "track": "System Reliability Hardening Track",
            "branch_expectation": "codex/post-phase7-hardening",
            "latest_runtime_run_id": run_id,
            "latest_recovery_live_order_id": recovery_bundle.get("live_order_id"),
            "packets": packets,
            "overall": {
                "status": "ok" if overall_ready else "partial",
                "ready_packet_count": sum(1 for item in packets if item["ready"]),
                "total_packet_count": len(packets),
                "all_ready": overall_ready,
            },
            "surfaces": {
                "operator_diagnostic_bundle": {
                    "run_id": operator_bundle.get("run_id"),
                    "cycle_id": operator_bundle.get("cycle_id"),
                    "consistency": consistency,
                },
                "recovery_replay_diagnostic_bundle": {
                    "live_order_id": recovery_bundle.get("live_order_id"),
                    "consistency": recovery_consistency,
                    "parity_summary": recovery_bundle.get("parity_summary"),
                },
            },
        }
