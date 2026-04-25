from __future__ import annotations

from ai_hedge_bot.core.ids import new_run_id


class ResponseDispatchAuditor:
    def build(self, incident: dict, payload: dict, approval_id: str | None, now: str) -> dict:
        target = "AFG" if payload.get("requires_approval") else "ORC_LOCAL_POLICY"
        status = "pending" if payload.get("requires_approval") else "succeeded"
        return {
            "dispatch_id": new_run_id(),
            "source_incident_id": incident["source_incident_id"],
            "approval_id": approval_id,
            "dispatch_target": target,
            "action": payload["proposed_action"],
            "dispatch_status": status,
            "idempotency_key": f"{approval_id or incident['source_incident_id']}:{payload['proposed_action']}:{target}",
            "error_message": "",
            "created_at": now,
            "dispatched_at": None if status == "pending" else now,
        }

