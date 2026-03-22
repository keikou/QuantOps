from __future__ import annotations

import json

from app.repositories.audit_repository import AuditRepository
from app.repositories.incident_repository import IncidentRepository


class IncidentService:
    def __init__(self, repository: IncidentRepository, audit_repository: AuditRepository) -> None:
        self.repository = repository
        self.audit_repository = audit_repository

    def list_incidents(self) -> dict:
        rows = self.repository.list_incidents()
        return {"count": len(rows), "items": rows}

    def create_incident(self, payload: dict) -> dict:
        result = self.repository.create_incident(payload)
        self.audit_repository.log_action(category="incidents", event_type="create", payload_json=json.dumps(result), actor_id="operator")
        return result

    def resolve(self, incident_id: str, note: str | None = None) -> dict:
        result = self.repository.resolve(incident_id, note=note)
        self.audit_repository.log_action(category="incidents", event_type="resolve", payload_json=json.dumps(result), actor_id="operator")
        return result
