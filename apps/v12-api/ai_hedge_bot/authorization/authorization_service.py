from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.authorization.actor_registry import ActorRegistry
from ai_hedge_bot.authorization.authorization_auditor import AuthorizationAuditor
from ai_hedge_bot.authorization.authorization_engine import AuthorizationEngine
from ai_hedge_bot.authorization.permission_registry import PermissionRegistry
from ai_hedge_bot.authorization.role_assignment import RoleAssignment
from ai_hedge_bot.authorization.role_registry import RoleRegistry


class AuthorizationService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.actors = ActorRegistry(self.store)
        self.roles = RoleRegistry(self.store)
        self.permissions = PermissionRegistry(self.store)
        self.assignments = RoleAssignment(self.store)
        self.engine = AuthorizationEngine(self.store)
        self.auditor = AuthorizationAuditor(self.store)
        self._seed_defaults()

    def check(
        self,
        actor_id: str = "operator",
        actor_type: str = "human",
        action: str = "approval.read",
        target_type: str = "system",
        target_id: str = "",
        scope: str = "global",
        risk_level: str = "LOW",
        source_system: str = "AFG",
        hard_safety_flag: bool = False,
    ) -> dict:
        actor = self.actors.get(actor_id)
        request = {
            "actor_id": actor_id,
            "actor_type": actor_type,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "scope": scope,
            "risk_level": risk_level,
            "source_system": source_system,
            "hard_safety_flag": hard_safety_flag,
        }
        decision = self.engine.evaluate(actor, self.assignments.active_roles(actor_id), request)
        row = self.auditor.persist(request, decision)
        return {"status": "ok", "authorization": {**decision, "decision_id": row["decision_id"]}}

    def latest(self, limit: int = 20) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM authorization_decisions ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "authorization_summary": {"decision_count": len(rows)}}

    def denials_latest(self, limit: int = 20) -> dict:
        rows = self.store.fetchall_dict(
            "SELECT * FROM authorization_decisions WHERE decision <> 'AUTHORIZED' ORDER BY created_at DESC LIMIT ?",
            [max(int(limit), 1)],
        )
        return {"status": "ok", "items": rows, "authorization_denial_summary": {"denial_count": len(rows)}}

    def roles_latest(self, limit: int = 100) -> dict:
        return {"status": "ok", "items": self.roles.latest(limit=limit)}

    def permissions_latest(self, limit: int = 200) -> dict:
        return {"status": "ok", "items": self.permissions.latest(limit=limit)}

    def assign_role(self, actor_id: str, role_id: str, scope: str = "global", target_id: str = "", actor_type: str = "human", operator_id: str = "codex") -> dict:
        authorization = self.check(actor_id=operator_id, action="role.assign", target_type="role", target_id=role_id, scope="global", risk_level="HIGH", source_system="AFG")
        if authorization.get("authorization", {}).get("decision") != "AUTHORIZED":
            return {"status": "authorization_denied", "authorization": authorization.get("authorization"), "actor_role": {}}
        self.actors.ensure(actor_id, actor_type=actor_type)
        self.roles.seed()
        row = self.assignments.assign(actor_id, role_id, scope=scope, target_id=target_id)
        self.auditor.persist({"actor_id": actor_id, "action": "role.assign", "target_type": "role", "target_id": role_id, "risk_level": "HIGH"}, {"decision": "AUTHORIZED", "reason": "role_assigned", "matched_roles": [role_id], "matched_permissions": ["role.assign"]})
        return {"status": "ok", "actor_role": row}

    def revoke_role(self, actor_id: str, role_id: str, scope: str = "global", target_id: str = "", operator_id: str = "codex") -> dict:
        authorization = self.check(actor_id=operator_id, action="role.revoke", target_type="role", target_id=role_id, scope="global", risk_level="HIGH", source_system="AFG")
        if authorization.get("authorization", {}).get("decision") != "AUTHORIZED":
            return {"status": "authorization_denied", "authorization": authorization.get("authorization"), "actor_role": {}}
        row = self.assignments.revoke(actor_id, role_id, scope=scope, target_id=target_id)
        self.auditor.persist({"actor_id": actor_id, "action": "role.revoke", "target_type": "role", "target_id": role_id, "risk_level": "HIGH"}, {"decision": "AUTHORIZED", "reason": "role_revoked", "matched_roles": [role_id], "matched_permissions": ["role.revoke"]})
        return {"status": "ok", "actor_role": row}

    def actor_permissions(self, actor_id: str) -> dict:
        assignments = self.assignments.active_roles(actor_id)
        permissions = []
        for assignment in assignments:
            role_permissions = self.store.fetchall_dict("SELECT permission_id FROM authorization_role_permissions WHERE role_id=?", [assignment.get("role_id")])
            permissions.extend(str(row.get("permission_id")) for row in role_permissions)
        return {"status": "ok", "actor_id": actor_id, "roles": assignments, "permissions": sorted(set(permissions))}

    def audit_latest(self, limit: int = 20) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM authorization_audit_log ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "authorization_audit_summary": {"audit_count": len(rows)}}

    def _seed_defaults(self) -> None:
        self.roles.seed()
        self.permissions.seed()
        defaults = [
            ("operator", "human", "OPERATOR"),
            ("codex", "human", "ADMIN"),
            ("system", "service", "ADMIN"),
            ("SERVICE_ORC", "service", "SERVICE_ORC"),
            ("SERVICE_AES", "service", "SERVICE_AES"),
            ("SERVICE_AAE", "service", "SERVICE_AAE"),
            ("SERVICE_LCC", "service", "SERVICE_LCC"),
            ("SERVICE_EXECUTION", "service", "SERVICE_EXECUTION"),
        ]
        for actor_id, actor_type, role_id in defaults:
            self.actors.ensure(actor_id, actor_type=actor_type)
            self.assignments.assign(actor_id, role_id)
