from __future__ import annotations

from ai_hedge_bot.core.ids import new_run_id


class ApprovalBridge:
    def build(self, incident: dict, payload: dict, now: str) -> dict | None:
        if not payload.get("requires_approval"):
            return None
        approval_id = new_run_id()
        return {
            "link_id": new_run_id(),
            "orc_incident_id": incident["source_incident_id"],
            "approval_id": approval_id,
            "proposed_action": payload["proposed_action"],
            "approval_status": "pending",
            "created_at": now,
            "decided_at": None,
        }

