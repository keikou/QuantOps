from __future__ import annotations

from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id


class ApprovalQueue:
    def __init__(self, store) -> None:
        self.store = store

    def create(self, payload: dict, policy: dict) -> dict:
        idempotency_key = payload.get("idempotency_key") or self._idempotency_key(payload)
        existing = self.store.fetchone_dict("SELECT * FROM pending_approvals WHERE idempotency_key=? LIMIT 1", [idempotency_key])
        if existing:
            return existing
        row = {
            "approval_id": payload.get("approval_id") or new_run_id(),
            "source_system": payload.get("source_system", "AFG"),
            "source_event_id": payload.get("source_event_id", ""),
            "target_type": payload.get("target_type", "system"),
            "target_id": payload.get("target_id", ""),
            "proposed_action": payload.get("proposed_action", payload.get("action_type", "review")),
            "risk_level": payload.get("risk_level", "L1_WATCH"),
            "requires_approval": bool(policy.get("requires_approval", True)),
            "status": "pending",
            "reason": payload.get("reason", policy.get("reason", "")),
            "payload_json": payload.get("payload_json", "{}"),
            "idempotency_key": idempotency_key,
            "created_at": utc_now_iso(),
            "decided_at": None,
            "decided_by": "",
        }
        self.store.append("pending_approvals", row)
        return row

    def latest(self, limit: int = 20) -> list[dict]:
        return self.store.fetchall_dict(
            "SELECT * FROM pending_approvals WHERE status='pending' ORDER BY created_at DESC LIMIT ?",
            [max(int(limit), 1)],
        )

    def get(self, approval_id: str) -> dict:
        return self.store.fetchone_dict("SELECT * FROM pending_approvals WHERE approval_id=? LIMIT 1", [approval_id]) or {}

    def decide(self, approval_id: str, status: str, operator_id: str) -> dict:
        now = utc_now_iso()
        self.store.execute(
            "UPDATE pending_approvals SET status=?, decided_at=?, decided_by=? WHERE approval_id=? AND status='pending'",
            [status, now, operator_id, approval_id],
        )
        return self.get(approval_id)

    def _idempotency_key(self, payload: dict) -> str:
        return ":".join(
            [
                str(payload.get("source_system", "")),
                str(payload.get("source_event_id", "")),
                str(payload.get("proposed_action", payload.get("action_type", ""))),
                str(payload.get("target_type", "")),
                str(payload.get("target_id", "")),
            ]
        )
