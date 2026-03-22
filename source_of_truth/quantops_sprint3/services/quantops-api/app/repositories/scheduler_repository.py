from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.repositories.duckdb import DuckDBConnectionFactory


class SchedulerRepository:
    def __init__(self, factory: DuckDBConnectionFactory) -> None:
        self.factory = factory

    def list_jobs(self) -> list[dict]:
        with self.factory.connect(read_only=True) as conn:
            rows = conn.execute(
                """
                SELECT job_id, job_name, job_group, cadence_type, cadence_value,
                       enabled, allow_manual_run, owner_service, CAST(updated_at AS VARCHAR)
                FROM scheduler_jobs
                ORDER BY job_group, job_name
                """
            ).fetchall()
        return [
            {
                "job_id": r[0], "job_name": r[1], "job_group": r[2], "cadence_type": r[3],
                "cadence_value": r[4], "enabled": r[5], "allow_manual_run": r[6],
                "owner_service": r[7], "updated_at": r[8],
            }
            for r in rows
        ]

    def upsert_job(self, payload: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        with self.factory.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO scheduler_jobs(
                    job_id, job_name, job_group, cadence_type, cadence_value,
                    enabled, allow_manual_run, owner_service, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    payload["job_id"], payload["job_name"], payload["job_group"], payload["cadence_type"],
                    payload["cadence_value"], payload.get("enabled", True), payload.get("allow_manual_run", True),
                    payload.get("owner_service", "quantops-scheduler"), now,
                ],
            )
        payload["updated_at"] = now
        return payload

    def delete_job(self, job_id: str) -> bool:
        with self.factory.connect() as conn:
            conn.execute("DELETE FROM scheduler_jobs WHERE job_id = ?", [job_id])
        return True

    def record_run(self, job_id: str, trigger_type: str, run_status: str = "completed") -> dict:
        run_id = f"run-{uuid4()}"
        started_at = datetime.now(timezone.utc)
        with self.factory.connect() as conn:
            conn.execute(
                """
                INSERT INTO scheduler_runs(
                    run_id, job_id, trigger_type, run_status, requested_by,
                    started_at, finished_at, duration_ms, result_json, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [run_id, job_id, trigger_type, run_status, "operator", started_at, started_at, 0, "{}", None],
            )
        return {"ok": True, "job_id": job_id, "run_id": run_id, "trigger_type": trigger_type, "run_status": run_status}
