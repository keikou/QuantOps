from __future__ import annotations

from ai_hedge_bot.core.clock import utc_now_iso


class RoleAssignment:
    def __init__(self, store) -> None:
        self.store = store

    def assign(self, actor_id: str, role_id: str, scope: str = "global", target_id: str = "", expires_at: str = "") -> dict:
        existing = self.store.fetchone_dict(
            """
            SELECT *
            FROM authorization_actor_roles
            WHERE actor_id=? AND role_id=? AND scope=? AND COALESCE(target_id, '')=?
            LIMIT 1
            """,
            [actor_id, role_id, scope, target_id],
        )
        if existing:
            self.store.execute(
                "UPDATE authorization_actor_roles SET active=TRUE, expires_at=? WHERE actor_id=? AND role_id=? AND scope=? AND COALESCE(target_id, '')=?",
                [expires_at or None, actor_id, role_id, scope, target_id],
            )
            return self.store.fetchone_dict("SELECT * FROM authorization_actor_roles WHERE actor_id=? AND role_id=? AND scope=? LIMIT 1", [actor_id, role_id, scope]) or {}
        row = {"actor_id": actor_id, "role_id": role_id, "scope": scope, "target_id": target_id, "active": True, "created_at": utc_now_iso(), "expires_at": expires_at or None}
        self.store.append("authorization_actor_roles", row)
        return row

    def revoke(self, actor_id: str, role_id: str, scope: str = "global", target_id: str = "") -> dict:
        self.store.execute(
            "UPDATE authorization_actor_roles SET active=FALSE WHERE actor_id=? AND role_id=? AND scope=? AND COALESCE(target_id, '')=?",
            [actor_id, role_id, scope, target_id],
        )
        return {"actor_id": actor_id, "role_id": role_id, "scope": scope, "target_id": target_id, "active": False}

    def active_roles(self, actor_id: str) -> list[dict]:
        return self.store.fetchall_dict(
            """
            SELECT ar.*, r.max_risk_level
            FROM authorization_actor_roles ar
            LEFT JOIN authorization_roles r ON ar.role_id = r.role_id
            WHERE ar.actor_id=? AND ar.active=TRUE
            ORDER BY ar.created_at DESC
            """,
            [actor_id],
        )

