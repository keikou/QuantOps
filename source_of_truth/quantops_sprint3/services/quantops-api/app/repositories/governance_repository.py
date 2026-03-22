from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
import json

from app.repositories.duckdb import DuckDBConnectionFactory


class GovernanceRepository:
    def __init__(self, factory: DuckDBConnectionFactory) -> None:
        self.factory = factory

    def insert_snapshot(self, payload: dict) -> dict:
        now = datetime.now(timezone.utc)
        with self.factory.connect() as conn:
            conn.execute("INSERT INTO governance_snapshots(snapshot_id, overview_json, created_at) VALUES (?, ?, ?)", [f"gov-{uuid4()}", json.dumps(payload), now])
        payload["as_of"] = now.isoformat()
        return payload

    def latest_snapshot(self) -> dict | None:
        with self.factory.connect(read_only=True) as conn:
            row = conn.execute("SELECT overview_json, CAST(created_at AS VARCHAR) FROM governance_snapshots ORDER BY created_at DESC LIMIT 1").fetchone()
        if row is None:
            return None
        payload = json.loads(row[0])
        payload["as_of"] = row[1]
        return payload

    def insert_review(self, strategy_id: str, review_type: str, recommendation: str, summary: dict) -> dict:
        now = datetime.now(timezone.utc)
        review = {"review_id": f"review-{uuid4()}", "strategy_id": strategy_id, "review_type": review_type, "recommendation": recommendation, "summary": summary, "created_at": now.isoformat()}
        with self.factory.connect() as conn:
            conn.execute("INSERT INTO promotion_reviews(review_id, strategy_id, review_type, recommendation, summary_json, created_at) VALUES (?, ?, ?, ?, ?, ?)", [review["review_id"], strategy_id, review_type, recommendation, json.dumps(summary), now])
        return review

    def list_reviews(self) -> list[dict]:
        with self.factory.connect(read_only=True) as conn:
            rows = conn.execute("SELECT review_id, strategy_id, review_type, recommendation, summary_json, CAST(created_at AS VARCHAR) FROM promotion_reviews ORDER BY created_at DESC").fetchall()
        return [{"review_id": r[0], "strategy_id": r[1], "review_type": r[2], "recommendation": r[3], "summary": json.loads(r[4]), "created_at": r[5]} for r in rows]
