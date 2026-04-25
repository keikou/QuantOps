from __future__ import annotations

from ai_hedge_bot.authorization.hard_safety_authorization import HardSafetyAuthorization
from ai_hedge_bot.authorization.risk_cap_checker import RiskCapChecker
from ai_hedge_bot.authorization.scope_matcher import ScopeMatcher
from ai_hedge_bot.authorization.service_actor_policy import ServiceActorPolicy


class AuthorizationEngine:
    def __init__(self, store) -> None:
        self.store = store
        self.scope = ScopeMatcher()
        self.risk = RiskCapChecker()
        self.service = ServiceActorPolicy()
        self.hard_safety = HardSafetyAuthorization()

    def evaluate(self, actor: dict, assignments: list[dict], request: dict) -> dict:
        if not actor:
            return self._decision("DENIED", "missing_actor")
        if not actor.get("active", False):
            return self._decision("DENIED", "inactive_actor")
        if not assignments:
            return self._decision("DENIED", "missing_active_role")
        action = str(request.get("action") or "")
        scope = str(request.get("scope") or request.get("target_type") or "global")
        target_id = str(request.get("target_id") or "")
        risk_level = str(request.get("risk_level") or "LOW")
        roles = [str(row.get("role_id")) for row in assignments]
        service_denial = self.service.denied(str(actor.get("actor_type")), roles, action, str(request.get("source_system") or ""))
        if service_denial:
            return self._decision("SERVICE_FORBIDDEN", service_denial, roles)
        hard_denial = self.hard_safety.denied(bool(request.get("hard_safety_flag", False)), action)
        if hard_denial:
            return self._decision("DENIED", hard_denial, roles)

        matched_permissions: list[str] = []
        scope_mismatch = False
        risk_mismatch = False
        for assignment in assignments:
            if not self.scope.allowed(assignment, scope, target_id):
                scope_mismatch = True
                continue
            if not self.risk.allowed(str(assignment.get("max_risk_level") or "LOW"), risk_level):
                risk_mismatch = True
                continue
            permissions = self._role_permissions(str(assignment.get("role_id")))
            if "*" in permissions or action in permissions:
                matched_permissions = ["*" if "*" in permissions else action]
                return self._decision("AUTHORIZED", "authorized_by_role_permission", roles, matched_permissions)
        if scope_mismatch:
            return self._decision("REQUIRE_SCOPE_MATCH", "no_matching_scope", roles)
        if risk_mismatch:
            return self._decision("REQUIRE_HIGHER_ROLE", "risk_level_exceeds_role_cap", roles)
        return self._decision("DENIED", "missing_permission", roles)

    def _role_permissions(self, role_id: str) -> set[str]:
        rows = self.store.fetchall_dict("SELECT permission_id FROM authorization_role_permissions WHERE role_id=?", [role_id])
        return {str(row.get("permission_id")) for row in rows}

    def _decision(self, decision: str, reason: str, roles: list[str] | None = None, permissions: list[str] | None = None) -> dict:
        return {
            "decision": decision,
            "reason": reason,
            "matched_roles": roles or [],
            "matched_permissions": permissions or [],
            "scope_allowed": decision == "AUTHORIZED",
            "risk_allowed": decision == "AUTHORIZED",
            "audit_required": True,
        }

