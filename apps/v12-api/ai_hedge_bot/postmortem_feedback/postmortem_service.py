from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id
from ai_hedge_bot.postmortem_feedback.feedback_builder import FeedbackBuilder
from ai_hedge_bot.postmortem_feedback.feedback_dispatcher import FeedbackDispatcher
from ai_hedge_bot.postmortem_feedback.schemas import IncidentLifecycle, normalize_severity


class PostmortemService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.builder = FeedbackBuilder()
        self.dispatcher = FeedbackDispatcher(self.store)

    def ingest(
        self,
        source_system: str = "ORC",
        source_event_id: str = "",
        severity: str = "S3",
        incident_type: str = "operational",
        affected_scope: str = "system",
        target_id: str = "",
        summary: str = "incident_detected",
        evidence_json: str = "{}",
    ) -> dict:
        existing = self._incident_by_source(source_system, source_event_id) if source_event_id else {}
        if existing:
            return {"status": "ok", "incident": existing, "idempotent": True}
        now = utc_now_iso()
        row = {
            "incident_id": new_run_id(),
            "source_system": source_system,
            "source_event_id": source_event_id,
            "severity": normalize_severity(severity),
            "incident_type": incident_type,
            "affected_scope": affected_scope,
            "target_id": target_id,
            "lifecycle_status": IncidentLifecycle.DETECTED.value,
            "summary": summary,
            "evidence_json": evidence_json,
            "detected_at": now,
            "created_at": now,
            "updated_at": now,
        }
        self.store.append("postmortem_incidents", row)
        return {"status": "ok", "incident": row, "idempotent": False}

    def incidents_latest(self, limit: int = 20) -> dict:
        rows = self._latest_rows("postmortem_incidents", limit)
        return {"status": "ok", "items": rows, "incident_summary": {"incident_count": len(rows)}}

    def review(self, incident_id: str, reviewer_id: str = "operator", findings_json: str = "{}", decision: str = "reviewed") -> dict:
        incident = self._incident(incident_id)
        if not incident:
            return {"status": "not_found", "incident_id": incident_id, "review": {}}
        now = utc_now_iso()
        row = {
            "review_id": new_run_id(),
            "incident_id": incident["incident_id"],
            "reviewer_id": reviewer_id,
            "lifecycle_status": IncidentLifecycle.REVIEWED.value,
            "findings_json": findings_json,
            "decision": decision,
            "created_at": now,
        }
        self.store.append("postmortem_reviews", row)
        self._update_lifecycle(incident["incident_id"], IncidentLifecycle.REVIEWED.value, now)
        return {"status": "ok", "review": row}

    def rca(
        self,
        incident_id: str,
        root_cause: str = "policy_gap",
        confidence: float = 0.8,
        approved: bool = True,
        contributing_factors_json: str = "[]",
        evidence_json: str = "{}",
    ) -> dict:
        incident = self._incident(incident_id)
        if not incident:
            return {"status": "not_found", "incident_id": incident_id, "rca": {}}
        now = utc_now_iso()
        row = {
            "rca_id": new_run_id(),
            "incident_id": incident["incident_id"],
            "root_cause": str(root_cause or "policy_gap").lower(),
            "contributing_factors_json": contributing_factors_json,
            "evidence_json": evidence_json,
            "confidence": float(confidence),
            "approved": bool(approved),
            "created_at": now,
            "approved_at": now if approved else None,
        }
        self.store.append("postmortem_rca", row)
        self._update_lifecycle(incident["incident_id"], IncidentLifecycle.RCA_COMPLETE.value if approved else IncidentLifecycle.REVIEWED.value, now)
        return {"status": "ok", "rca": row}

    def actions(
        self,
        incident_id: str,
        target_system: str = "AFG_POLICY",
        action_type: str = "policy_rule_add",
        owner: str = "operator",
        payload_json: str = "{}",
        due_at: str | None = None,
    ) -> dict:
        incident = self._incident(incident_id)
        if not incident:
            return {"status": "not_found", "incident_id": incident_id, "action_item": {}}
        rca = self._latest_rca(incident["incident_id"])
        now = utc_now_iso()
        row = {
            "action_item_id": new_run_id(),
            "incident_id": incident["incident_id"],
            "rca_id": rca.get("rca_id", ""),
            "target_system": target_system,
            "action_type": action_type,
            "owner": owner,
            "status": "open",
            "due_at": due_at,
            "payload_json": payload_json,
            "created_at": now,
            "updated_at": now,
        }
        self.store.append("postmortem_action_items", row)
        self._update_lifecycle(incident["incident_id"], IncidentLifecycle.ACTION_DEFINED.value, now)
        return {"status": "ok", "action_item": row}

    def close(self, incident_id: str, operator_id: str = "operator", reason: str = "postmortem_closed", emit_feedback: bool = True) -> dict:
        incident = self._incident(incident_id)
        if not incident:
            return {"status": "not_found", "incident_id": incident_id, "incident": {}}
        rca = self._latest_rca(incident["incident_id"])
        if incident.get("severity") in {"S1", "S2"} and not bool(rca.get("approved")):
            return {"status": "blocked", "reason": "high_severity_incident_requires_approved_rca", "incident": incident}
        feedback_result = {"items": [], "dispatches": []}
        if emit_feedback:
            feedback_result = self.build_feedback(incident["incident_id"])
            dispatches = []
            for feedback in feedback_result.get("items", []):
                dispatches.append(self.dispatch_feedback(str(feedback.get("feedback_id"))).get("dispatch", {}))
            feedback_result["dispatches"] = dispatches
        now = utc_now_iso()
        lifecycle = IncidentLifecycle.FEEDBACK_EMITTED.value if feedback_result.get("items") else IncidentLifecycle.CLOSED.value
        self._update_lifecycle(incident["incident_id"], lifecycle, now)
        closed = self._incident(incident["incident_id"])
        return {"status": "ok", "incident": closed, "feedback": feedback_result, "closed_by": operator_id, "reason": reason}

    def build_feedback(self, incident_id: str) -> dict:
        incident = self._incident(incident_id)
        if not incident:
            return {"status": "not_found", "incident_id": incident_id, "items": []}
        rca = self._latest_rca(incident["incident_id"])
        if not bool(rca.get("approved")):
            return {"status": "invalid_rca", "reason": "approved_rca_required", "items": []}
        actions = self._action_items(incident["incident_id"])
        items = []
        for feedback in self.builder.build(incident, rca, actions):
            existing = self.store.fetchone_dict("SELECT * FROM postmortem_feedback WHERE feedback_id=? LIMIT 1", [feedback.feedback_id])
            if existing:
                items.append(existing)
                continue
            row = feedback.to_row()
            self.store.append("postmortem_feedback", row)
            items.append(row)
        return {"status": "ok", "items": items, "postmortem_feedback_summary": {"feedback_count": len(items)}}

    def dispatch_feedback(self, feedback_id: str, approved: bool = False) -> dict:
        feedback = self._feedback(feedback_id)
        if not feedback:
            return {"status": "not_found", "feedback_id": feedback_id, "dispatch": {}}
        if approved and not bool(feedback.get("approved")):
            now = utc_now_iso()
            self.store.execute(
                "UPDATE postmortem_feedback SET approved=TRUE, approved_at=? WHERE feedback_id=?",
                [now, feedback_id],
            )
            feedback = self._feedback(feedback_id)
        dispatch = self.dispatcher.dispatch(feedback)
        return {"status": "ok", "dispatch": dispatch, "feedback": feedback}

    def postmortem_latest(self, limit: int = 20) -> dict:
        return {
            "status": "ok",
            "incidents": self._latest_rows("postmortem_incidents", limit),
            "reviews": self._latest_rows("postmortem_reviews", limit),
            "rca": self._latest_rows("postmortem_rca", limit),
            "action_items": self._latest_rows("postmortem_action_items", limit),
            "feedback": self._latest_rows("postmortem_feedback", limit),
            "dispatches": self._latest_rows("postmortem_feedback_dispatch", limit),
        }

    def feedback_latest(self, limit: int = 20) -> dict:
        rows = self._latest_rows("postmortem_feedback", limit)
        return {"status": "ok", "items": rows, "postmortem_feedback_summary": {"feedback_count": len(rows)}}

    def feedback_by_target(self, target_system: str, limit: int = 20) -> dict:
        rows = self.store.fetchall_dict(
            "SELECT * FROM postmortem_feedback WHERE target_system=? ORDER BY created_at DESC LIMIT ?",
            [str(target_system).upper(), max(int(limit), 1)],
        )
        return {"status": "ok", "target_system": str(target_system).upper(), "items": rows, "postmortem_feedback_summary": {"feedback_count": len(rows)}}

    def dispatch_latest(self, limit: int = 20) -> dict:
        rows = self._latest_rows("postmortem_feedback_dispatch", limit)
        return {"status": "ok", "items": rows, "postmortem_feedback_dispatch_summary": {"dispatch_count": len(rows)}}

    def _incident(self, incident_id: str) -> dict:
        return self.store.fetchone_dict(
            "SELECT * FROM postmortem_incidents WHERE incident_id=? OR source_event_id=? ORDER BY created_at DESC LIMIT 1",
            [incident_id, incident_id],
        ) or {}

    def _incident_by_source(self, source_system: str, source_event_id: str) -> dict:
        return self.store.fetchone_dict(
            "SELECT * FROM postmortem_incidents WHERE source_system=? AND source_event_id=? ORDER BY created_at DESC LIMIT 1",
            [source_system, source_event_id],
        ) or {}

    def _latest_rca(self, incident_id: str) -> dict:
        return self.store.fetchone_dict("SELECT * FROM postmortem_rca WHERE incident_id=? ORDER BY created_at DESC LIMIT 1", [incident_id]) or {}

    def _action_items(self, incident_id: str) -> list[dict]:
        return self.store.fetchall_dict("SELECT * FROM postmortem_action_items WHERE incident_id=? ORDER BY created_at DESC", [incident_id])

    def _feedback(self, feedback_id: str) -> dict:
        return self.store.fetchone_dict("SELECT * FROM postmortem_feedback WHERE feedback_id=? LIMIT 1", [feedback_id]) or {}

    def _latest_rows(self, table: str, limit: int) -> list[dict]:
        return self.store.fetchall_dict(
            f"SELECT * FROM {table} ORDER BY created_at DESC LIMIT ?",
            [max(int(limit), 1)],
        )

    def _update_lifecycle(self, incident_id: str, lifecycle: str, now: str) -> None:
        self.store.execute(
            "UPDATE postmortem_incidents SET lifecycle_status=?, updated_at=? WHERE incident_id=?",
            [lifecycle, now, incident_id],
        )
