from __future__ import annotations

import json

from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id


class AuthorizationAuditor:
    def __init__(self, store) -> None:
        self.store = store

    def persist(self, request: dict, decision: dict) -> dict:
        now = utc_now_iso()
        row = {
            "decision_id": new_run_id(),
            "actor_id": request.get("actor_id"),
            "action": request.get("action"),
            "target_type": request.get("target_type"),
            "target_id": request.get("target_id"),
            "risk_level": request.get("risk_level"),
            "decision": decision["decision"],
            "reason": decision["reason"],
            "matched_roles": ",".join(decision.get("matched_roles", [])),
            "matched_permissions": ",".join(decision.get("matched_permissions", [])),
            "created_at": now,
        }
        self.store.append("authorization_decisions", row)
        self.store.append(
            "authorization_audit_log",
            {
                "audit_id": new_run_id(),
                "actor_id": request.get("actor_id"),
                "event_type": "authorization_check",
                "action": request.get("action"),
                "target_type": request.get("target_type"),
                "target_id": request.get("target_id"),
                "decision": decision["decision"],
                "metadata_json": json.dumps({"request": request, "decision": decision}, ensure_ascii=False, default=str),
                "created_at": now,
            },
        )
        return row

