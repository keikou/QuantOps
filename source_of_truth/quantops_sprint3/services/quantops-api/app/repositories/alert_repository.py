from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
import json

from app.repositories.duckdb import DuckDBConnectionFactory


class AlertRepository:
    def __init__(self, factory: DuckDBConnectionFactory) -> None:
        self.factory = factory

    def create_alert(self, payload: dict) -> dict:
        now = datetime.now(timezone.utc)
        alert_id = payload.get("alert_id") or f"alert-{uuid4()}"
        with self.factory.connect() as conn:
            conn.execute(
                """INSERT INTO alerts(alert_id, alert_type, severity, source_service, source, title, message, status, payload_json, created_at, resolved_at, acknowledged_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [alert_id, payload["alert_type"], payload["severity"], payload.get("source_service", "quantops-api"), payload.get("source", payload.get("source_service", "quantops-api")), payload["title"], payload.get("message"), payload.get("status", "open"), json.dumps(payload.get("payload", {})), now, None, None],
            )
            conn.execute(
                """INSERT INTO alert_events(event_id, alert_id, event_type, actor_id, note, created_at) VALUES (?, ?, ?, ?, ?, ?)""",
                [f"ae-{uuid4()}", alert_id, "created", payload.get("actor_id", "system"), payload.get("message"), now],
            )
        return {**payload, "alert_id": alert_id, "created_at": now.isoformat(), "status": payload.get("status", "open")}

    def list_alerts(self) -> list[dict]:
        with self.factory.connect(read_only=True) as conn:
            rows = conn.execute(
                """SELECT alert_id, alert_type, severity, COALESCE(source, source_service), title, message, status, payload_json, CAST(created_at AS VARCHAR), CAST(acknowledged_at AS VARCHAR), CAST(resolved_at AS VARCHAR) FROM alerts ORDER BY created_at DESC"""
            ).fetchall()
        return [{"alert_id": r[0], "alert_type": r[1], "severity": r[2], "source": r[3], "title": r[4], "message": r[5], "status": r[6], "payload": json.loads(r[7] or '{}'), "created_at": r[8], "acknowledged_at": r[9], "resolved_at": r[10]} for r in rows]

    def update_status(self, alert_id: str, status: str, actor_id: str = "operator", note: str | None = None) -> dict:
        now = datetime.now(timezone.utc)
        ack = now if status == "acknowledged" else None
        resolved = now if status == "resolved" else None
        with self.factory.connect() as conn:
            if status == "acknowledged":
                conn.execute("UPDATE alerts SET status = ?, acknowledged_at = COALESCE(acknowledged_at, ?) WHERE alert_id = ?", [status, now, alert_id])
            elif status == "resolved":
                conn.execute("UPDATE alerts SET status = ?, resolved_at = ? WHERE alert_id = ?", [status, now, alert_id])
            else:
                conn.execute("UPDATE alerts SET status = ? WHERE alert_id = ?", [status, alert_id])
            conn.execute("INSERT INTO alert_events(event_id, alert_id, event_type, actor_id, note, created_at) VALUES (?, ?, ?, ?, ?, ?)", [f"ae-{uuid4()}", alert_id, status, actor_id, note, now])
        return {"ok": True, "alert_id": alert_id, "status": status, "updated_at": now.isoformat(), "acknowledged_at": ack.isoformat() if ack else None, "resolved_at": resolved.isoformat() if resolved else None}
