from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
import json

from app.repositories.duckdb import DuckDBConnectionFactory


class ApprovalRepository:
    def __init__(self, factory: DuckDBConnectionFactory) -> None:
        self.factory = factory

    def create_request(self, payload: dict) -> dict:
        now = datetime.now(timezone.utc)
        request_id = payload.get("request_id") or f"req-{uuid4()}"
        with self.factory.connect() as conn:
            conn.execute("INSERT INTO approval_requests(request_id, request_type, target_id, status, requested_by, summary_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", [request_id, payload["request_type"], payload["target_id"], payload.get("status", "pending"), payload.get("requested_by", "operator"), json.dumps(payload.get("summary", {})), now])
        return {**payload, "request_id": request_id, "status": payload.get("status", "pending"), "created_at": now.isoformat()}

    def list_requests(self) -> list[dict]:
        with self.factory.connect(read_only=True) as conn:
            rows = conn.execute("SELECT request_id, request_type, target_id, status, requested_by, summary_json, CAST(created_at AS VARCHAR) FROM approval_requests ORDER BY created_at DESC").fetchall()
        return [{"request_id": r[0], "request_type": r[1], "target_id": r[2], "status": r[3], "requested_by": r[4], "summary": json.loads(r[5]), "created_at": r[6]} for r in rows]

    def decide(self, request_id: str, decision: str, actor_id: str = "operator", note: str | None = None) -> dict:
        now = datetime.now(timezone.utc)
        with self.factory.connect() as conn:
            conn.execute("UPDATE approval_requests SET status = ? WHERE request_id = ?", [decision, request_id])
            conn.execute("INSERT INTO approval_decisions(decision_id, request_id, decision, actor_id, note, created_at) VALUES (?, ?, ?, ?, ?, ?)", [f"decision-{uuid4()}", request_id, decision, actor_id, note, now])
        return {"ok": True, "request_id": request_id, "status": decision, "updated_at": now.isoformat()}
