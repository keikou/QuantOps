from __future__ import annotations

import json

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id
from ai_hedge_bot.operational_governance.approval_bridge import ApprovalBridge
from ai_hedge_bot.operational_governance.governance_payload_builder import GovernancePayloadBuilder
from ai_hedge_bot.operational_governance.incident_audit_loader import IncidentAuditLoader
from ai_hedge_bot.operational_governance.incident_lifecycle_engine import IncidentLifecycleEngine
from ai_hedge_bot.operational_governance.override_sync import OverrideSync
from ai_hedge_bot.operational_governance.recovery_governance import RecoveryGovernance
from ai_hedge_bot.operational_governance.response_dispatch_auditor import ResponseDispatchAuditor


class OperationalGovernanceService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.loader = IncidentAuditLoader(self.store)
        self.payloads = GovernancePayloadBuilder()
        self.approvals = ApprovalBridge()
        self.overrides = OverrideSync(self.store)
        self.dispatch = ResponseDispatchAuditor()
        self.recovery = RecoveryGovernance()
        self.lifecycle = IncidentLifecycleEngine()

    def sync(self, limit: int = 50) -> dict:
        run_id = new_run_id()
        started_at = utc_now_iso()
        now = utc_now_iso()
        incidents = self.loader.load(limit=limit)
        governance_rows = []
        approval_rows = []
        audit_rows = []
        dispatch_rows = []

        for incident in incidents:
            if not incident.get("source_incident_id"):
                continue
            if self._existing_incident(str(incident["source_incident_id"])):
                continue
            payload = self.payloads.build(incident)
            approval = self.approvals.build(incident, payload, now)
            approval_id = approval.get("approval_id") if approval else ""
            governance_status = self.lifecycle.status_for(bool(payload["requires_approval"]))
            governance_rows.append(
                {
                    "governance_incident_id": new_run_id(),
                    "source_incident_id": incident["source_incident_id"],
                    "source_system": incident.get("source_system"),
                    "incident_type": incident.get("incident_type"),
                    "risk_level": incident.get("risk_level"),
                    "affected_scope": incident.get("affected_scope"),
                    "target_id": incident.get("target_id"),
                    "governance_status": governance_status,
                    "approval_id": approval_id,
                    "operator_id": "",
                    "reason": payload["reason"],
                    "created_at": now,
                    "updated_at": now,
                }
            )
            if approval:
                approval_rows.append(approval)
                audit_rows.append(self._audit(incident, "approval_created", payload["proposed_action"], now, payload))
            audit_rows.append(self._audit(incident, "incident_detected", payload["proposed_action"], now, payload))
            audit_rows.append(self._audit(incident, "response_recommended", payload["proposed_action"], now, payload))
            dispatch_rows.append(self.dispatch.build(incident, payload, approval_id, now))

        if governance_rows:
            self.store.append("orc_governance_incidents", governance_rows)
        if approval_rows:
            self.store.append("orc_afg_approval_links", approval_rows)
        if audit_rows:
            self.store.append("orc_governance_audit_events", audit_rows)
        if dispatch_rows:
            self.store.append("orc_response_dispatch_audit", dispatch_rows)

        overrides = self.overrides.latest_active(limit=20)
        self.store.append(
            "orc_governance_sync_runs",
            {
                "run_id": run_id,
                "started_at": started_at,
                "completed_at": utc_now_iso(),
                "incident_count": len(governance_rows),
                "approval_created_count": len(approval_rows),
                "audit_event_count": len(audit_rows),
                "override_count": len(overrides),
                "status": "ok",
                "notes": "orc05_incident_audit_operator_governance_bridge",
            },
        )
        return self.latest(limit=limit)

    def latest(self, limit: int = 20) -> dict:
        run = self._latest_run()
        if not run:
            return self.sync(limit=limit)
        incidents = self._latest_rows("orc_governance_incidents", limit)
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "governance_incidents": incidents,
            "orc_governance_summary": {
                "incident_count": run.get("incident_count"),
                "approval_created_count": run.get("approval_created_count"),
                "audit_event_count": run.get("audit_event_count"),
                "override_count": run.get("override_count"),
            },
            "as_of": run.get("completed_at"),
        }

    def incidents_latest(self, limit: int = 20) -> dict:
        self._ensure_run()
        rows = self._latest_rows("orc_governance_incidents", limit)
        return {"status": "ok", "items": rows, "orc_governance_incident_summary": {"incident_count": len(rows)}}

    def incident(self, incident_id: str) -> dict:
        self._ensure_run()
        row = self.store.fetchone_dict(
            """
            SELECT *
            FROM orc_governance_incidents
            WHERE governance_incident_id=? OR source_incident_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [incident_id, incident_id],
        ) or {}
        return {"status": "ok" if row else "not_found", "incident_id": incident_id, "governance_incident": row}

    def pending_approvals_latest(self, limit: int = 20) -> dict:
        self._ensure_run()
        rows = self.store.fetchall_dict(
            """
            SELECT *
            FROM orc_afg_approval_links
            WHERE approval_status='pending'
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [max(int(limit), 1)],
        )
        return {"status": "ok", "items": rows, "pending_approval_summary": {"approval_count": len(rows)}}

    def audit_latest(self, limit: int = 20) -> dict:
        self._ensure_run()
        rows = self._latest_rows("orc_governance_audit_events", limit)
        return {"status": "ok", "items": rows, "audit_summary": {"audit_event_count": len(rows)}}

    def request_recovery(
        self,
        source_incident_id: str = "latest",
        requested_target_level: str = "L1_WATCH",
        operator_id: str = "operator",
    ) -> dict:
        self._ensure_run()
        incident = self._latest_incident() if source_incident_id == "latest" else self.incident(source_incident_id).get("governance_incident", {})
        current_risk_level = str(incident.get("risk_level") or "L0_NORMAL")
        readiness_passed = current_risk_level in {"L0_NORMAL", "L1_WATCH", "L2_REDUCE"}
        row = self.recovery.build_request(
            source_incident_id=str(incident.get("source_incident_id") or source_incident_id),
            current_risk_level=current_risk_level,
            requested_target_level=requested_target_level,
            readiness_passed=readiness_passed,
            now=utc_now_iso(),
        )
        row["operator_id"] = operator_id
        self.store.append("orc_recovery_governance", row)
        self.store.append(
            "orc_governance_audit_events",
            self._audit(
                {
                    "source_incident_id": row["source_incident_id"],
                    "source_system": "ORC-05",
                    "risk_level": current_risk_level,
                    "affected_scope": "system",
                    "target_id": row["source_incident_id"],
                },
                "recovery_requested",
                requested_target_level,
                utc_now_iso(),
                row,
                operator_id=operator_id,
            ),
        )
        return {"status": "ok", "recovery_request": row}

    def recovery_latest(self, limit: int = 20) -> dict:
        rows = self._latest_rows("orc_recovery_governance", limit)
        return {"status": "ok", "items": rows, "recovery_governance_summary": {"recovery_count": len(rows)}}

    def _audit(self, incident: dict, event_type: str, action: str, now: str, metadata: dict, operator_id: str = "") -> dict:
        return {
            "audit_id": new_run_id(),
            "source_system": incident.get("source_system") or "ORC",
            "source_event_id": incident.get("source_incident_id"),
            "event_type": event_type,
            "risk_level": incident.get("risk_level"),
            "action": action,
            "target_scope": incident.get("affected_scope"),
            "target_id": incident.get("target_id"),
            "operator_id": operator_id,
            "metadata_json": json.dumps(metadata, ensure_ascii=False, default=str),
            "created_at": now,
        }

    def _latest_run(self) -> dict:
        return self.store.fetchone_dict(
            """
            SELECT *
            FROM orc_governance_sync_runs
            ORDER BY completed_at DESC, started_at DESC
            LIMIT 1
            """
        ) or {}

    def _latest_rows(self, table: str, limit: int) -> list[dict]:
        return self.store.fetchall_dict(
            f"""
            SELECT *
            FROM {table}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [max(int(limit), 1)],
        )

    def _existing_incident(self, source_incident_id: str) -> bool:
        row = self.store.fetchone_dict(
            "SELECT source_incident_id FROM orc_governance_incidents WHERE source_incident_id=? LIMIT 1",
            [source_incident_id],
        )
        return bool(row)

    def _latest_incident(self) -> dict:
        return self.store.fetchone_dict("SELECT * FROM orc_governance_incidents ORDER BY created_at DESC LIMIT 1") or {}

    def _ensure_run(self) -> dict:
        run = self._latest_run()
        if not run:
            self.sync(limit=20)
            run = self._latest_run()
        return run
