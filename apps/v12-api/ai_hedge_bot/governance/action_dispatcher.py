from __future__ import annotations

from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id


class ActionDispatcher:
    def __init__(self, store) -> None:
        self.store = store

    def dispatch(self, approval: dict, target_system: str = "local_staging", dry_run: bool = True) -> dict:
        now = utc_now_iso()
        action = approval.get("proposed_action") or approval.get("action_type") or "review"
        row = {
            "dispatch_id": new_run_id(),
            "approval_id": approval.get("approval_id", ""),
            "source_system": approval.get("source_system", "AFG"),
            "target_system": target_system,
            "action": action,
            "target_type": approval.get("target_type", "system"),
            "target_id": approval.get("target_id", ""),
            "payload_json": approval.get("payload_json", "{}"),
            "idempotency_key": f"{approval.get('approval_id', '')}:{target_system}:{action}",
            "dry_run": dry_run,
            "dispatch_status": "dry_run" if dry_run else "staged",
            "error_message": "",
            "created_at": now,
            "dispatched_at": now,
        }
        self.store.append("governance_dispatch_log", row)
        if approval.get("approval_id"):
            self.store.execute(
                "UPDATE pending_approvals SET status=? WHERE approval_id=? AND status IN ('approved','pending')",
                ["dispatched" if not dry_run else "dry_run", approval.get("approval_id")],
            )
        return row

