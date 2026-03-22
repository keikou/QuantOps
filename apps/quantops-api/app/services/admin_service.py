from __future__ import annotations

from app.repositories.audit_repository import AuditRepository


class AdminService:
    def __init__(self, audit_repository: AuditRepository) -> None:
        self.audit_repository = audit_repository

    def get_audit_logs(self) -> dict:
        return {"items": self.audit_repository.list_audit_logs()}

    def get_operator_actions(self) -> dict:
        return {"items": self.audit_repository.list_operator_actions()}

    def get_config_changes(self) -> dict:
        return {"items": self.audit_repository.list_config_changes()}

    def get_mode_switches(self) -> dict:
        return {"items": self.audit_repository.list_mode_switches(), "kill_switch_events": self.audit_repository.list_kill_switch_events()}
