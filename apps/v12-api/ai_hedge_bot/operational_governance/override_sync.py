from __future__ import annotations


class OverrideSync:
    def __init__(self, store) -> None:
        self.store = store

    def latest_active(self, limit: int = 20) -> list[dict]:
        return self.store.fetchall_dict(
            """
            SELECT *
            FROM operational_risk_overrides
            WHERE active=TRUE
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [max(int(limit), 1)],
        )

