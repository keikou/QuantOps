from __future__ import annotations


class IncidentLifecycleEngine:
    def status_for(self, requires_approval: bool) -> str:
        return "approval_pending" if requires_approval else "auto_applied"

