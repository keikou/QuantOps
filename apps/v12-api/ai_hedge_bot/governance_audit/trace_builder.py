from __future__ import annotations

from typing import Any


class TraceBuilder:
    def build_decision_trace(self, components: dict[str, Any]) -> list[dict[str, Any]]:
        trace: list[dict[str, Any]] = []
        incident = components.get("incident") or {}
        if incident:
            trace.append(
                {
                    "step": "incident_ingested",
                    "id": incident.get("incident_id"),
                    "severity": incident.get("severity"),
                    "lifecycle_status": incident.get("lifecycle_status"),
                    "created_at": incident.get("created_at"),
                }
            )
        for review in components.get("reviews") or []:
            trace.append({"step": "review_recorded", "id": review.get("review_id"), "decision": review.get("decision"), "created_at": review.get("created_at")})
        for rca in components.get("rca") or []:
            trace.append({"step": "rca_recorded", "id": rca.get("rca_id"), "root_cause": rca.get("root_cause"), "approved": rca.get("approved"), "created_at": rca.get("created_at")})
        for action in components.get("action_items") or []:
            trace.append({"step": "action_item_defined", "id": action.get("action_item_id"), "target_system": action.get("target_system"), "status": action.get("status"), "created_at": action.get("created_at")})
        return trace

    def build_approval_trace(self, components: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "step": "approval_evidence",
                "id": approval.get("approval_id"),
                "status": approval.get("status"),
                "approver": approval.get("decided_by"),
                "source_event_id": approval.get("source_event_id"),
                "created_at": approval.get("created_at"),
            }
            for approval in components.get("approvals") or []
        ]

    def build_feedback_trace(self, components: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "step": "feedback_generated",
                "id": feedback.get("feedback_id"),
                "target_system": feedback.get("target_system"),
                "feedback_type": feedback.get("feedback_type"),
                "requires_approval": feedback.get("requires_approval"),
                "created_at": feedback.get("created_at"),
            }
            for feedback in components.get("feedback") or []
        ]

    def build_dispatch_trace(self, components: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "step": "feedback_dispatched",
                "id": dispatch.get("dispatch_id"),
                "feedback_id": dispatch.get("feedback_id"),
                "status": dispatch.get("dispatch_status"),
                "target_record_id": dispatch.get("target_record_id"),
                "created_at": dispatch.get("created_at"),
            }
            for dispatch in components.get("dispatch") or []
        ]

