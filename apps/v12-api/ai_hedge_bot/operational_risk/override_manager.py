from __future__ import annotations

from ai_hedge_bot.core.ids import new_run_id


class OverrideManager:
    def build(self, operator_id: str, override_scope: str, override_reason: str, expires_at: str = "") -> dict:
        return {
            "override_id": new_run_id(),
            "operator_id": operator_id,
            "override_scope": override_scope,
            "override_reason": override_reason,
            "expires_at": expires_at,
            "active": bool(override_reason),
        }

