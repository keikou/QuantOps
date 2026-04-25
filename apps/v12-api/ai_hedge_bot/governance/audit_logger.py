from __future__ import annotations

from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id


class AuditLogger:
    def __init__(self, store) -> None:
        self.store = store

    def log(
        self,
        event_type: str,
        source_system: str = "AFG",
        source_event_id: str = "",
        target_type: str = "system",
        target_id: str = "",
        action: str = "",
        operator_id: str = "",
        decision: str = "",
        risk_level: str = "",
        metadata_json: str = "{}",
    ) -> dict:
        row = {
            "log_id": new_run_id(),
            "event_type": event_type,
            "source_system": source_system,
            "source_event_id": source_event_id,
            "target_type": target_type,
            "target_id": target_id,
            "action": action,
            "operator_id": operator_id,
            "decision": decision,
            "risk_level": risk_level,
            "metadata_json": metadata_json,
            "created_at": utc_now_iso(),
        }
        self.store.append("governance_audit_log", row)
        return row

