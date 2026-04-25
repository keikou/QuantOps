from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id


class OperatorOverrideManager:
    def __init__(self, store) -> None:
        self.store = store

    def create(
        self,
        target_type: str,
        target_id: str,
        override_action: str,
        reason: str,
        operator_id: str,
        risk_level: str = "L1_WATCH",
        ttl_hours: int = 4,
    ) -> dict:
        blocked = not reason or not operator_id or ttl_hours <= 0
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=max(ttl_hours, 1))).isoformat()
        row = {
            "override_id": new_run_id(),
            "target_type": target_type,
            "target_id": target_id,
            "override_action": override_action,
            "reason": reason,
            "operator_id": operator_id,
            "risk_level": risk_level,
            "expires_at": expires_at,
            "active": not blocked,
            "blocked_by_policy": blocked,
            "created_at": utc_now_iso(),
            "expired_at": None,
        }
        self.store.append("operator_overrides", row)
        return row

    def latest(self, limit: int = 20) -> list[dict]:
        return self.store.fetchall_dict("SELECT * FROM operator_overrides ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])

    def expire(self, override_id: str) -> dict:
        now = utc_now_iso()
        self.store.execute("UPDATE operator_overrides SET active=FALSE, expired_at=? WHERE override_id=?", [now, override_id])
        return self.store.fetchone_dict("SELECT * FROM operator_overrides WHERE override_id=? LIMIT 1", [override_id]) or {}

