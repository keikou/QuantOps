from __future__ import annotations

from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id


class GovernanceStateEngine:
    def __init__(self, store) -> None:
        self.store = store

    def compute(self) -> dict:
        pending = self._count("pending_approvals", "status='pending'")
        active_overrides = self._count("operator_overrides", "active=TRUE")
        blocked = self._count("operator_actions", "status='blocked'")
        last_action = self.store.fetchone_dict("SELECT action_id FROM operator_actions ORDER BY created_at DESC LIMIT 1") or {}
        last_risk = self.store.fetchone_dict("SELECT risk_level FROM pending_approvals ORDER BY created_at DESC LIMIT 1") or {}
        mode = "HALTED" if str(last_risk.get("risk_level")) == "L5_GLOBAL_HALT" else "RESTRICTED" if pending else "NORMAL"
        row = {
            "state_id": new_run_id(),
            "global_mode": mode,
            "approval_required_level": "L4_PARTIAL_HALT",
            "active_override_count": active_overrides,
            "pending_approval_count": pending,
            "blocked_action_count": blocked,
            "last_operator_action_id": last_action.get("action_id", ""),
            "last_orc_risk_level": last_risk.get("risk_level", "L0_NORMAL"),
            "created_at": utc_now_iso(),
        }
        self.store.append("governance_state", row)
        return row

    def _count(self, table: str, where: str) -> int:
        row = self.store.fetchone_dict(f"SELECT COUNT(*) AS n FROM {table} WHERE {where}") or {}
        return int(row.get("n") or 0)

