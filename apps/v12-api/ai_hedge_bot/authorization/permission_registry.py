from __future__ import annotations

from ai_hedge_bot.core.clock import utc_now_iso


DEFAULT_PERMISSIONS = {
    "VIEWER": ["approval.read", "governance.state.read"],
    "OPERATOR": ["approval.read", "approval.approve.low", "approval.approve.medium", "approval.reject", "override.create.low", "override.expire", "operator.action.submit"],
    "RISK_MANAGER": ["approval.read", "approval.approve.low", "approval.approve.medium", "approval.approve.high", "approval.reject", "override.create.low", "override.create.high", "override.expire", "risk_response.approve", "recovery.approve", "policy.tighten.risk"],
    "EXECUTION_MANAGER": ["approval.read", "approval.approve.low", "approval.approve.medium", "approval.approve.high", "approval.reject", "override.create.low", "override.create.high", "override.expire", "dispatch.execute", "execution.safe_mode.apply"],
    "RESEARCH_MANAGER": ["approval.read", "approval.approve.low", "approval.approve.medium", "approval.approve.high", "approval.reject", "alpha.promote", "alpha.retire", "policy.update.generation_prior"],
    "ADMIN": ["*"],
    "EMERGENCY_CONTROLLER": ["freeze_new_exposure", "partial_halt", "global_halt", "reduce_only", "approval.approve.critical"],
    "SERVICE_ORC": ["approval.request.create", "risk_response.request"],
    "SERVICE_AES": ["policy.recommendation.create"],
    "SERVICE_AAE": ["alpha.promotion.request"],
    "SERVICE_LCC": ["capital.enforcement.report"],
    "SERVICE_EXECUTION": ["execution.enforcement.report"],
}


class PermissionRegistry:
    def __init__(self, store) -> None:
        self.store = store

    def seed(self) -> None:
        for permissions in DEFAULT_PERMISSIONS.values():
            for action in permissions:
                self.ensure(action)
        for role, permissions in DEFAULT_PERMISSIONS.items():
            for action in permissions:
                perm = self.ensure(action)
                self.assign(role, perm["permission_id"])

    def ensure(self, action: str, target_type: str = "global", scope: str = "global", max_risk_level: str = "CRITICAL") -> dict:
        existing = self.store.fetchone_dict("SELECT * FROM authorization_permissions WHERE action=? LIMIT 1", [action])
        if existing:
            return existing
        row = {
            "permission_id": action,
            "permission_name": action,
            "action": action,
            "target_type": target_type,
            "scope": scope,
            "max_risk_level": max_risk_level,
            "created_at": utc_now_iso(),
        }
        self.store.append("authorization_permissions", row)
        return row

    def assign(self, role_id: str, permission_id: str) -> None:
        existing = self.store.fetchone_dict(
            "SELECT * FROM authorization_role_permissions WHERE role_id=? AND permission_id=? LIMIT 1",
            [role_id, permission_id],
        )
        if not existing:
            self.store.append("authorization_role_permissions", {"role_id": role_id, "permission_id": permission_id, "created_at": utc_now_iso()})

    def latest(self, limit: int = 200) -> list[dict]:
        return self.store.fetchall_dict("SELECT * FROM authorization_permissions ORDER BY action ASC LIMIT ?", [max(int(limit), 1)])

