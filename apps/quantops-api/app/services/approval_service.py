from __future__ import annotations

import json

from app.repositories.approval_repository import ApprovalRepository
from app.repositories.audit_repository import AuditRepository


class ApprovalService:
    def __init__(self, repository: ApprovalRepository, audit_repository: AuditRepository) -> None:
        self.repository = repository
        self.audit_repository = audit_repository

    def list_requests(self) -> dict:
        rows = self.repository.list_requests()
        return {"count": len(rows), "items": rows}

    def create_request(self, payload: dict) -> dict:
        req = self.repository.create_request(payload)
        self.audit_repository.log_action(category="approval", event_type="request", payload_json=json.dumps(req), actor_id=req.get("requested_by", "operator"))
        return req

    def approve(self, request_id: str, actor_id: str = "operator", note: str | None = None) -> dict:
        result = self.repository.decide(request_id, "approved", actor_id=actor_id, note=note)
        self.audit_repository.log_action(category="approval", event_type="approve", payload_json=json.dumps(result), actor_id=actor_id)
        return result

    def reject(self, request_id: str, actor_id: str = "operator", note: str | None = None) -> dict:
        result = self.repository.decide(request_id, "rejected", actor_id=actor_id, note=note)
        self.audit_repository.log_action(category="approval", event_type="reject", payload_json=json.dumps(result), actor_id=actor_id)
        return result
