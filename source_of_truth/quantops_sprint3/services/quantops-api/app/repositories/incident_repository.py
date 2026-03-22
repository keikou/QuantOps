from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
import json

from app.repositories.duckdb import DuckDBConnectionFactory


class IncidentRepository:
    def __init__(self, factory: DuckDBConnectionFactory) -> None:
        self.factory = factory

    def create_incident(self, payload: dict) -> dict:
        now = datetime.now(timezone.utc)
        incident_id = payload.get("incident_id") or f"inc-{uuid4()}"
        with self.factory.connect() as conn:
            conn.execute("INSERT INTO incidents(incident_id, incident_type, severity, status, title, description, created_at, resolved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [incident_id, payload["incident_type"], payload["severity"], payload.get("status", "open"), payload["title"], payload.get("description"), now, None])
            conn.execute("INSERT INTO incident_events(event_id, incident_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?, ?)", [f"ince-{uuid4()}", incident_id, "created", json.dumps(payload), now])
        return {**payload, "incident_id": incident_id, "status": payload.get("status", "open"), "created_at": now.isoformat()}

    def list_incidents(self) -> list[dict]:
        with self.factory.connect(read_only=True) as conn:
            rows = conn.execute("SELECT incident_id, incident_type, severity, status, title, description, CAST(created_at AS VARCHAR), CAST(resolved_at AS VARCHAR) FROM incidents ORDER BY created_at DESC").fetchall()
        return [{"incident_id": r[0], "incident_type": r[1], "severity": r[2], "status": r[3], "title": r[4], "description": r[5], "created_at": r[6], "resolved_at": r[7]} for r in rows]

    def resolve(self, incident_id: str, note: str | None = None) -> dict:
        now = datetime.now(timezone.utc)
        with self.factory.connect() as conn:
            conn.execute("UPDATE incidents SET status = 'resolved', resolved_at = ? WHERE incident_id = ?", [now, incident_id])
            conn.execute("INSERT INTO incident_events(event_id, incident_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?, ?)", [f"ince-{uuid4()}", incident_id, "resolved", json.dumps({"note": note}), now])
        return {"ok": True, "incident_id": incident_id, "status": "resolved", "updated_at": now.isoformat()}
