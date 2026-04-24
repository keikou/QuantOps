from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER


class SynthesisRunRepository:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def insert_run(self, payload: dict) -> None:
        self.store.append("alpha_synthesis_runs", payload)

    def latest_run(self, generator_type: str | None = None) -> dict:
        if generator_type:
            return self.store.fetchone_dict(
                """
                SELECT *
                FROM alpha_synthesis_runs
                WHERE generator_type=?
                ORDER BY completed_at DESC, started_at DESC
                LIMIT 1
                """,
                [generator_type],
            ) or {}
        return self.store.fetchone_dict(
            """
            SELECT *
            FROM alpha_synthesis_runs
            ORDER BY completed_at DESC, started_at DESC
            LIMIT 1
            """
        ) or {}

    def list_recent_candidates(self, limit: int = 100, generator_type: str | None = None) -> list[dict]:
        if generator_type:
            return self.store.fetchall_dict(
                """
                SELECT *
                FROM alpha_synthesis_candidates
                WHERE generator_type=?
                ORDER BY created_at DESC, candidate_id ASC
                LIMIT ?
                """,
                [generator_type, max(int(limit), 1)],
            )
        return self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_synthesis_candidates
            ORDER BY created_at DESC, candidate_id ASC
            LIMIT ?
            """,
            [max(int(limit), 1)],
        )

    def list_recent_novelty(self, limit: int = 100) -> list[dict]:
        return self.store.fetchall_dict(
            """
            SELECT *
            FROM alpha_synthesis_novelty
            ORDER BY created_at DESC, novelty_id ASC
            LIMIT ?
            """,
            [max(int(limit), 1)],
        )
