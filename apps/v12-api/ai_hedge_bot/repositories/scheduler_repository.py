from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_hedge_bot.app.container import CONTAINER


DEFAULT_JOBS = [
    {'job_id': 'paper_cycle', 'job_name': 'paper_cycle', 'cadence': 'manual', 'enabled': True, 'owner_service': 'v12-worker', 'mode': 'paper'},
    {'job_id': 'shadow_cycle', 'job_name': 'shadow_cycle', 'cadence': 'manual', 'enabled': True, 'owner_service': 'v12-worker', 'mode': 'shadow'},
    {'job_id': 'nightly_weights', 'job_name': 'nightly_weights', 'cadence': '0 0 * * *', 'enabled': True, 'owner_service': 'v12-worker', 'mode': 'paper'},
]


@dataclass
class SchedulerRepository:
    def __post_init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def seed_defaults(self, now_iso: str) -> None:
        existing = self.store.fetchone_dict("SELECT COUNT(*) AS count FROM scheduler_jobs")
        if existing and int(existing.get('count', 0)) > 0:
            return
        for row in DEFAULT_JOBS:
            payload = dict(row)
            payload['updated_at'] = now_iso
            self.store.append('scheduler_jobs', payload)

    def list_jobs(self) -> list[dict[str, Any]]:
        return self.store.fetchall_dict(
            "SELECT job_id, job_name, cadence, enabled, owner_service, mode, updated_at FROM scheduler_jobs ORDER BY job_name"
        )

    def create_run(self, row: dict[str, Any]) -> None:
        self.store.append('scheduler_runs', row)

    def finalize_run(self, scheduler_run_id: str, *, status: str, finished_at: str, duration_ms: int, error_message: str | None = None, run_id: str | None = None) -> None:
        self.store.execute(
            """
            UPDATE scheduler_runs
            SET status = ?, finished_at = ?, duration_ms = ?, error_message = ?, run_id = COALESCE(?, run_id)
            WHERE scheduler_run_id = ?
            """,
            [status, finished_at, duration_ms, error_message, run_id, scheduler_run_id],
        )

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.store.fetchall_dict(
            """
            SELECT scheduler_run_id, job_id, run_id, trigger_type, status, started_at, finished_at, duration_ms, error_message
            FROM scheduler_runs
            ORDER BY started_at DESC
            LIMIT ?
            """,
            [limit],
        )
