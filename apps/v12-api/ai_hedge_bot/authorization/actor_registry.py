from __future__ import annotations

from ai_hedge_bot.core.clock import utc_now_iso


class ActorRegistry:
    def __init__(self, store) -> None:
        self.store = store

    def ensure(self, actor_id: str, actor_type: str = "human", display_name: str = "") -> dict:
        existing = self.get(actor_id)
        if existing:
            return existing
        row = {"actor_id": actor_id, "actor_type": actor_type, "display_name": display_name or actor_id, "active": True, "created_at": utc_now_iso()}
        self.store.append("authorization_actors", row)
        return row

    def get(self, actor_id: str) -> dict:
        return self.store.fetchone_dict("SELECT * FROM authorization_actors WHERE actor_id=? LIMIT 1", [actor_id]) or {}

    def active(self, limit: int = 100) -> list[dict]:
        return self.store.fetchall_dict("SELECT * FROM authorization_actors WHERE active=TRUE ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])

