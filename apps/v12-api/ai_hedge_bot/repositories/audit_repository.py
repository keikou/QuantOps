from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_hedge_bot.app.container import CONTAINER


@dataclass
class AuditRepository:
    def __post_init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def create_log(self, row: dict[str, Any]) -> None:
        self.store.append('audit_logs', row)

    def list_logs(self, run_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        if run_id:
            return self.store.fetchall_dict(
                "SELECT audit_id, category, event_type, run_id, created_at, payload_json, actor FROM audit_logs WHERE run_id = ? ORDER BY created_at DESC LIMIT ?",
                [run_id, limit],
            )
        return self.store.fetchall_dict(
            "SELECT audit_id, category, event_type, run_id, created_at, payload_json, actor FROM audit_logs ORDER BY created_at DESC LIMIT ?",
            [limit],
        )
