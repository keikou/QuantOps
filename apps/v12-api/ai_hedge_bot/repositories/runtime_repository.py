from __future__ import annotations

import json
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

    def create_event(self, row: dict[str, Any]) -> None:
        event_id = str(row.get("event_id") or "")
        if event_id:
            existing = self.store.fetchone_dict(
                "SELECT event_id FROM runtime_events WHERE event_id = ? LIMIT 1",
                [event_id],
            )
            if existing:
                return
        payload = dict(row)
        payload["details_json"] = self.store.to_json(payload.get("details_json") or {})
        self.store.append("runtime_events", payload)

    def create_events(self, rows: list[dict[str, Any]]) -> None:
        for row in rows:
            self.create_event(row)

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

    def list_events(
        self,
        *,
        limit: int = 50,
        run_id: str | None = None,
        event_type: str | None = None,
        symbol: str | None = None,
        reason_only: bool = False,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if run_id:
            clauses.append("run_id = ?")
            params.append(run_id)
        if event_type:
            clauses.append("event_type = ?")
            params.append(event_type)
        if symbol:
            clauses.append("symbol = ?")
            params.append(symbol)
        if reason_only:
            clauses.append("coalesce(reason_code, '') <> ''")
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.store.fetchall_dict(
            f"""
            SELECT event_id, run_id, cycle_id, event_type, reason_code, symbol, mode, source,
                   status, severity, summary, details_json,
                   CAST(timestamp AS VARCHAR) AS timestamp,
                   CAST(created_at AS VARCHAR) AS created_at
            FROM runtime_events
            {where_sql}
            ORDER BY timestamp DESC, created_at DESC
            LIMIT ?
            """,
            [*params, limit],
        )
        for row in rows:
            details_json = row.get("details_json")
            if isinstance(details_json, str) and details_json:
                try:
                    row["details"] = json.loads(details_json)
                except Exception:
                    row["details"] = {}
            else:
                row["details"] = details_json or {}
            row.pop("details_json", None)
        return rows
