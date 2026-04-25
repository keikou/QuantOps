from __future__ import annotations

import json

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.authorization.authorization_service import AuthorizationService
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id
from ai_hedge_bot.governance.action_dispatcher import ActionDispatcher
from ai_hedge_bot.governance.approval_queue import ApprovalQueue
from ai_hedge_bot.governance.audit_logger import AuditLogger
from ai_hedge_bot.governance.governance_state_engine import GovernanceStateEngine
from ai_hedge_bot.governance.override_manager import OperatorOverrideManager
from ai_hedge_bot.governance.policy_gate_engine import PolicyGateEngine


class GovernanceService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.policy = PolicyGateEngine()
        self.approvals = ApprovalQueue(self.store)
        self.audit = AuditLogger(self.store)
        self.overrides = OperatorOverrideManager(self.store)
        self.dispatcher = ActionDispatcher(self.store)
        self.state = GovernanceStateEngine(self.store)
        self.authorization = AuthorizationService()

    def submit_action(
        self,
        action_type: str = "review",
        target_type: str = "system",
        target_id: str = "",
        source_system: str = "Operator",
        risk_level: str = "L1_WATCH",
        reason: str = "operator_action",
        operator_id: str = "operator",
        payload_json: str = "{}",
    ) -> dict:
        current_state = self.governance_state_latest().get("governance_state", {})
        decision = self.policy.evaluate(source_system, action_type, target_type, risk_level, current_state.get("global_mode", "NORMAL"), operator_id, reason)
        now = utc_now_iso()
        row = {
            "action_id": new_run_id(),
            "action_type": action_type,
            "target_type": target_type,
            "target_id": target_id,
            "decision": decision["decision"],
            "reason": reason or decision["reason"],
            "operator_id": operator_id,
            "source_system": source_system,
            "risk_level": risk_level,
            "status": self._status_for_decision(decision["decision"]),
            "payload_json": payload_json,
            "created_at": now,
            "applied_at": now if decision["decision"] == "AUTO_APPLY" else None,
        }
        self.store.append("operator_actions", row)
        approval = {}
        if decision["requires_approval"]:
            approval = self.approvals.create(
                {
                    "source_system": source_system,
                    "source_event_id": row["action_id"],
                    "target_type": target_type,
                    "target_id": target_id,
                    "proposed_action": action_type,
                    "risk_level": risk_level,
                    "reason": reason,
                    "payload_json": payload_json,
                },
                decision,
            )
        self.audit.log("operator_action_submitted", source_system, row["action_id"], target_type, target_id, action_type, operator_id, decision["decision"], risk_level, json.dumps(decision))
        self.state.compute()
        return {"status": "ok", "operator_action": row, "policy_decision": decision, "pending_approval": approval}

    def operator_actions_latest(self, limit: int = 20) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM operator_actions ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "operator_action_summary": {"action_count": len(rows)}}

    def pending_approvals_latest(self, limit: int = 20) -> dict:
        rows = self.approvals.latest(limit=limit)
        return {"status": "ok", "items": rows, "pending_approval_summary": {"approval_count": len(rows)}}

    def pending_approval(self, approval_id: str) -> dict:
        row = self.approvals.get(approval_id)
        return {"status": "ok" if row else "not_found", "approval_id": approval_id, "pending_approval": row}

    def approve(self, approval_id: str, operator_id: str = "operator", reason: str = "approved") -> dict:
        current = self.approvals.get(approval_id)
        authorization = self.authorization.check(
            actor_id=operator_id,
            action=self._approval_action(str(current.get("risk_level") or "LOW")),
            target_type=str(current.get("target_type") or "system"),
            target_id=str(current.get("target_id") or ""),
            scope=str(current.get("target_type") or "global"),
            risk_level=str(current.get("risk_level") or "LOW"),
            source_system=str(current.get("source_system") or "AFG"),
        )
        if authorization.get("authorization", {}).get("decision") != "AUTHORIZED":
            return {"status": "authorization_denied", "authorization": authorization.get("authorization"), "approval": current}
        row = self.approvals.decide(approval_id, "approved", operator_id)
        self.audit.log("operator_approved", row.get("source_system", "AFG"), row.get("source_event_id", approval_id), row.get("target_type", ""), row.get("target_id", ""), row.get("proposed_action", ""), operator_id, "approved", row.get("risk_level", ""), json.dumps({"reason": reason}))
        self.state.compute()
        return {"status": "ok" if row else "not_found", "approval": row}

    def reject(self, approval_id: str, operator_id: str = "operator", reason: str = "rejected") -> dict:
        current = self.approvals.get(approval_id)
        authorization = self.authorization.check(
            actor_id=operator_id,
            action="approval.reject",
            target_type=str(current.get("target_type") or "system"),
            target_id=str(current.get("target_id") or ""),
            scope=str(current.get("target_type") or "global"),
            risk_level=str(current.get("risk_level") or "LOW"),
            source_system=str(current.get("source_system") or "AFG"),
        )
        if authorization.get("authorization", {}).get("decision") != "AUTHORIZED":
            return {"status": "authorization_denied", "authorization": authorization.get("authorization"), "approval": current}
        row = self.approvals.decide(approval_id, "rejected", operator_id)
        self.audit.log("operator_rejected", row.get("source_system", "AFG"), row.get("source_event_id", approval_id), row.get("target_type", ""), row.get("target_id", ""), row.get("proposed_action", ""), operator_id, "rejected", row.get("risk_level", ""), json.dumps({"reason": reason}))
        self.state.compute()
        return {"status": "ok" if row else "not_found", "approval": row}

    def create_override(
        self,
        target_type: str = "system",
        target_id: str = "global",
        override_action: str = "allow_reduce_only",
        reason: str = "operator_override",
        operator_id: str = "operator",
        risk_level: str = "L1_WATCH",
        ttl_hours: int = 4,
    ) -> dict:
        authorization = self.authorization.check(
            actor_id=operator_id,
            action=self._override_action(risk_level),
            target_type=target_type,
            target_id=target_id,
            scope=target_type,
            risk_level=risk_level,
            source_system="Operator",
        )
        if authorization.get("authorization", {}).get("decision") != "AUTHORIZED":
            return {"status": "authorization_denied", "authorization": authorization.get("authorization"), "operator_override": {}}
        row = self.overrides.create(target_type, target_id, override_action, reason, operator_id, risk_level, ttl_hours)
        self.audit.log("operator_override_created", "Operator", row["override_id"], target_type, target_id, override_action, operator_id, "blocked" if row["blocked_by_policy"] else "active", risk_level, json.dumps(row, default=str))
        self.state.compute()
        return {"status": "ok", "operator_override": row}

    def operator_overrides_latest(self, limit: int = 20) -> dict:
        rows = self.overrides.latest(limit=limit)
        return {"status": "ok", "items": rows, "operator_override_summary": {"override_count": len(rows)}}

    def expire_override(self, override_id: str, operator_id: str = "operator") -> dict:
        authorization = self.authorization.check(actor_id=operator_id, action="override.expire", target_type="operator_override", target_id=override_id, scope="global", risk_level="LOW", source_system="Operator")
        if authorization.get("authorization", {}).get("decision") != "AUTHORIZED":
            return {"status": "authorization_denied", "authorization": authorization.get("authorization"), "operator_override": {}}
        row = self.overrides.expire(override_id)
        self.audit.log("operator_override_expired", "Operator", override_id, row.get("target_type", ""), row.get("target_id", ""), row.get("override_action", ""), operator_id, "expired", row.get("risk_level", ""), json.dumps(row, default=str))
        self.state.compute()
        return {"status": "ok" if row else "not_found", "operator_override": row}

    def audit_log_latest(self, limit: int = 20) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM governance_audit_log ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "audit_log_summary": {"event_count": len(rows)}}

    def governance_state_latest(self) -> dict:
        row = self.store.fetchone_dict("SELECT * FROM governance_state ORDER BY created_at DESC LIMIT 1")
        if not row:
            row = self.state.compute()
        return {"status": "ok", "governance_state": row}

    def sync(self, limit: int = 50) -> dict:
        links = self.store.fetchall_dict(
            """
            SELECT *
            FROM orc_afg_approval_links
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [max(int(limit), 1)],
        )
        created = 0
        for link in links:
            incident = self.store.fetchone_dict(
                "SELECT * FROM orc_governance_incidents WHERE source_incident_id=? ORDER BY created_at DESC LIMIT 1",
                [link.get("orc_incident_id")],
            ) or {}
            payload = {
                "approval_id": link.get("approval_id"),
                "source_system": "ORC",
                "source_event_id": link.get("orc_incident_id"),
                "target_type": incident.get("affected_scope", "risk_response"),
                "target_id": incident.get("target_id", ""),
                "proposed_action": link.get("proposed_action"),
                "risk_level": incident.get("risk_level", "L4_PARTIAL_HALT"),
                "reason": incident.get("reason", "orc_governance_sync"),
                "payload_json": json.dumps({"orc_approval_link": link, "orc_incident": incident}, default=str),
            }
            before = self.approvals.get(str(link.get("approval_id")))
            self.approvals.create(payload, {"requires_approval": True, "reason": payload["reason"]})
            if not before:
                created += 1
        self.audit.log("governance_sync", "AFG", "orc_afg_approval_links", "system", "governance", "sync", "system", "AUTO_RECORD", "L1_WATCH", json.dumps({"links_seen": len(links), "created": created}))
        state = self.state.compute()
        return {"status": "ok", "sync_summary": {"links_seen": len(links), "pending_created": created}, "governance_state": state}

    def dispatch(self, approval_id: str = "latest", target_system: str = "local_staging", dry_run: bool = True) -> dict:
        approval = self._latest_approval() if approval_id == "latest" else self.approvals.get(approval_id)
        if not approval:
            return {"status": "not_found", "approval_id": approval_id, "dispatch": {}}
        authorization = self.authorization.check(actor_id="system", actor_type="service", action="dispatch.execute", target_type=str(approval.get("target_type") or "system"), target_id=str(approval.get("target_id") or ""), scope=str(approval.get("target_type") or "global"), risk_level=str(approval.get("risk_level") or "LOW"), source_system="AFG")
        if authorization.get("authorization", {}).get("decision") != "AUTHORIZED":
            return {"status": "authorization_denied", "authorization": authorization.get("authorization"), "dispatch": {}}
        row = self.dispatcher.dispatch(approval, target_system=target_system, dry_run=dry_run)
        self.audit.log("dispatch_attempted", "AFG", approval.get("approval_id", ""), approval.get("target_type", ""), approval.get("target_id", ""), approval.get("proposed_action", ""), "system", row["dispatch_status"], approval.get("risk_level", ""), json.dumps(row, default=str))
        self.state.compute()
        return {"status": "ok", "dispatch": row}

    def dispatch_latest(self, limit: int = 20) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM governance_dispatch_log ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "dispatch_summary": {"dispatch_count": len(rows)}}

    def _latest_approval(self) -> dict:
        return self.store.fetchone_dict("SELECT * FROM pending_approvals ORDER BY created_at DESC LIMIT 1") or {}

    def _status_for_decision(self, decision: str) -> str:
        return {
            "AUTO_RECORD": "auto_recorded",
            "AUTO_APPLY": "auto_applied",
            "REQUIRE_APPROVAL": "approval_pending",
            "BLOCK": "blocked",
        }.get(decision, "recorded")

    def _approval_action(self, risk_level: str) -> str:
        if risk_level in {"L5_GLOBAL_HALT", "CRITICAL"}:
            return "approval.approve.critical"
        if risk_level in {"L3_FREEZE", "L4_PARTIAL_HALT", "HIGH"}:
            return "approval.approve.high"
        if risk_level in {"L2_REDUCE", "MEDIUM"}:
            return "approval.approve.medium"
        return "approval.approve.low"

    def _override_action(self, risk_level: str) -> str:
        if risk_level in {"L5_GLOBAL_HALT", "CRITICAL"}:
            return "override.create.critical"
        if risk_level in {"L3_FREEZE", "L4_PARTIAL_HALT", "HIGH"}:
            return "override.create.high"
        return "override.create.low"
