from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_hedge_bot.app.container import CONTAINER


@dataclass
class RuntimeRepository:
    def __post_init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def create_run(self, row: dict[str, Any]) -> None:
        self.store.append('runtime_runs', row)

    def update_run(self, run_id: str, *, status: str, finished_at: str, duration_ms: int, error_message: str | None = None) -> None:
        self.store.execute(
            """
            UPDATE runtime_runs
            SET status = ?, finished_at = ?, duration_ms = ?, error_message = ?
            WHERE run_id = ?
            """,
            [status, finished_at, duration_ms, error_message, run_id],
        )

    def create_step(self, row: dict[str, Any]) -> None:
        self.store.append('runtime_run_steps', row)

    def update_step(self, step_id: str, *, status: str, finished_at: str, duration_ms: int, error_message: str | None = None, payload_json: str | None = None) -> None:
        self.store.execute(
            """
            UPDATE runtime_run_steps
            SET status = ?, finished_at = ?, duration_ms = ?, error_message = ?, payload_json = ?
            WHERE step_id = ?
            """,
            [status, finished_at, duration_ms, error_message, payload_json, step_id],
        )

    def create_checkpoint(self, row: dict[str, Any]) -> None:
        self.store.append('runtime_checkpoints', row)

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.store.fetchall_dict(
            """
            SELECT run_id, job_name, mode, started_at, finished_at, status, error_message, duration_ms, triggered_by, created_at
            FROM runtime_runs
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [limit],
        )

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        run = self.store.fetchone_dict(
            """
            SELECT run_id, job_name, mode, started_at, finished_at, status, error_message, duration_ms, triggered_by, created_at
            FROM runtime_runs WHERE run_id = ?
            """,
            [run_id],
        )
        if not run:
            return None
        run['steps'] = self.store.fetchall_dict(
            """
            SELECT step_id, step_name, status, started_at, finished_at, duration_ms, error_message, payload_json
            FROM runtime_run_steps WHERE run_id = ? ORDER BY started_at ASC
            """,
            [run_id],
        )
        run['checkpoints'] = self.store.fetchall_dict(
            """
            SELECT checkpoint_id, checkpoint_name, created_at, payload_json
            FROM runtime_checkpoints WHERE run_id = ? ORDER BY created_at ASC
            """,
            [run_id],
        )
        run['audit_logs'] = self.store.fetchall_dict(
            """
            SELECT audit_id, category, event_type, run_id, created_at, payload_json, actor
            FROM audit_logs WHERE run_id = ? ORDER BY created_at ASC
            """,
            [run_id],
        )
        return run
