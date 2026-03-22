from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
import json

from app.repositories.duckdb import DuckDBConnectionFactory


class MonitoringRepository:
    def __init__(self, factory: DuckDBConnectionFactory) -> None:
        self.factory = factory

    def insert_snapshot(self, payload: dict) -> dict:
        now = datetime.now(timezone.utc)
        snapshot_id = f"mon-{uuid4()}"
        with self.factory.connect() as conn:
            conn.execute(
                """INSERT INTO monitoring_snapshots(snapshot_id, system_status, execution_status, services_json, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)""",
                [snapshot_id, payload["system_status"], payload["execution_status"], json.dumps(payload.get("services", {})), json.dumps(payload), now],
            )
            for service_name, detail in (payload.get("services") or {}).items():
                conn.execute(
                    """INSERT INTO service_status_snapshots(snapshot_id, service_name, service_status, detail_json, created_at) VALUES (?, ?, ?, ?, ?)""",
                    [f"svc-{uuid4()}", service_name, str(detail), json.dumps({"status": detail}), now],
                )
        payload["as_of"] = now.isoformat()
        return payload

    def latest_snapshot(self) -> dict | None:
        with self.factory.connect(read_only=True) as conn:
            row = conn.execute("SELECT system_status, execution_status, services_json, payload_json, CAST(created_at AS VARCHAR) FROM monitoring_snapshots ORDER BY created_at DESC LIMIT 1").fetchone()
        if row is None:
            return None
        payload = json.loads(row[3])
        payload["system_status"] = row[0]
        payload["execution_status"] = row[1]
        payload["services"] = json.loads(row[2])
        payload["as_of"] = row[4]
        return payload

    def latest_service_statuses(self) -> list[dict]:
        with self.factory.connect(read_only=True) as conn:
            rows = conn.execute(
                """SELECT service_name, service_status, detail_json, CAST(created_at AS VARCHAR) FROM service_status_snapshots ORDER BY created_at DESC LIMIT 20"""
            ).fetchall()
        return [{"service_name": r[0], "service_status": r[1], "detail": json.loads(r[2]), "as_of": r[3]} for r in rows]
