from __future__ import annotations


class ScopeMatcher:
    def allowed(self, role_assignment: dict, scope: str, target_id: str) -> bool:
        assigned_scope = str(role_assignment.get("scope") or "global")
        assigned_target = str(role_assignment.get("target_id") or "")
        if assigned_scope == "global":
            return True
        if assigned_scope != scope:
            return False
        if assigned_target and assigned_target != target_id:
            return False
        return True

