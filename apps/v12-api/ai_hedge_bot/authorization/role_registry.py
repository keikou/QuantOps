from __future__ import annotations

from ai_hedge_bot.authorization.schemas import DEFAULT_ROLE_CAPS
from ai_hedge_bot.core.clock import utc_now_iso


class RoleRegistry:
    def __init__(self, store) -> None:
        self.store = store

    def seed(self) -> None:
        for role_name, cap in DEFAULT_ROLE_CAPS.items():
            self.ensure(role_name, cap)

    def ensure(self, role_name: str, max_risk_level: str) -> dict:
        existing = self.get(role_name)
        if existing:
            return existing
        row = {
            "role_id": role_name,
            "role_name": role_name,
            "description": f"default role {role_name}",
            "max_risk_level": max_risk_level,
            "created_at": utc_now_iso(),
        }
        self.store.append("authorization_roles", row)
        return row

    def get(self, role_id: str) -> dict:
        return self.store.fetchone_dict("SELECT * FROM authorization_roles WHERE role_id=? OR role_name=? LIMIT 1", [role_id, role_id]) or {}

    def latest(self, limit: int = 100) -> list[dict]:
        return self.store.fetchall_dict("SELECT * FROM authorization_roles ORDER BY role_name ASC LIMIT ?", [max(int(limit), 1)])

