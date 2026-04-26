from __future__ import annotations

from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id
from ai_hedge_bot.governance.approval_queue import ApprovalQueue
from ai_hedge_bot.postmortem_feedback.aes_feedback_adapter import AESFeedbackAdapter
from ai_hedge_bot.postmortem_feedback.afg_policy_feedback_adapter import AFGPolicyFeedbackAdapter
from ai_hedge_bot.postmortem_feedback.execution_feedback_adapter import ExecutionFeedbackAdapter
from ai_hedge_bot.postmortem_feedback.lcc_feedback_adapter import LCCFeedbackAdapter
from ai_hedge_bot.postmortem_feedback.orc_feedback_adapter import ORCFeedbackAdapter
from ai_hedge_bot.postmortem_feedback.schemas import dispatch_idempotency_key, severity_to_risk_level


class FeedbackDispatcher:
    def __init__(self, store) -> None:
        self.store = store
        self.approvals = ApprovalQueue(store)
        self.adapters = {
            "AES": AESFeedbackAdapter(),
            "ORC": ORCFeedbackAdapter(),
            "AFG_POLICY": AFGPolicyFeedbackAdapter(),
            "LCC": LCCFeedbackAdapter(),
            "EXECUTION": ExecutionFeedbackAdapter(),
        }

    def dispatch(self, feedback: dict) -> dict:
        if not feedback:
            return {}
        if bool(feedback.get("requires_approval")) and not bool(feedback.get("approved")):
            return self._stage_for_approval(feedback)
        adapter = self.adapters.get(str(feedback.get("target_system") or "").upper())
        if adapter is None:
            return self._persist_dispatch(feedback, "staged_local", "", "unknown_target_system")
        result = adapter.dispatch(feedback)
        return self._persist_dispatch(
            feedback,
            str(result.get("dispatch_status") or "staged"),
            str(result.get("target_record_id") or ""),
            str(result.get("error_message") or ""),
        )

    def _stage_for_approval(self, feedback: dict) -> dict:
        idempotency_key = dispatch_idempotency_key(feedback)
        approval = self.approvals.create(
            {
                "source_system": "AFG-04",
                "source_event_id": feedback.get("feedback_id"),
                "target_type": str(feedback.get("target_system") or "postmortem_feedback").lower(),
                "target_id": feedback.get("incident_id"),
                "proposed_action": feedback.get("feedback_type"),
                "risk_level": severity_to_risk_level(str(feedback.get("severity") or "S3")),
                "reason": "postmortem_feedback_requires_approval",
                "payload_json": feedback.get("payload_json") or "{}",
                "idempotency_key": idempotency_key,
            },
            {"requires_approval": True, "reason": "postmortem_feedback_requires_approval"},
        )
        return self._persist_dispatch(feedback, "pending_approval", str(approval.get("approval_id") or ""), "")

    def _persist_dispatch(self, feedback: dict, status: str, target_record_id: str, error_message: str) -> dict:
        idempotency_key = dispatch_idempotency_key(feedback)
        existing = self.store.fetchone_dict("SELECT * FROM postmortem_feedback_dispatch WHERE idempotency_key=? LIMIT 1", [idempotency_key])
        if existing:
            if existing.get("dispatch_status") == "pending_approval" and status != "pending_approval":
                now = utc_now_iso()
                self.store.execute(
                    """
                    UPDATE postmortem_feedback_dispatch
                    SET dispatch_status=?, target_record_id=?, error_message=?, dispatched_at=?
                    WHERE idempotency_key=?
                    """,
                    [status, target_record_id, error_message, now, idempotency_key],
                )
                return self.store.fetchone_dict("SELECT * FROM postmortem_feedback_dispatch WHERE idempotency_key=? LIMIT 1", [idempotency_key]) or existing
            return existing
        now = utc_now_iso()
        row = {
            "dispatch_id": new_run_id(),
            "feedback_id": feedback.get("feedback_id"),
            "target_system": feedback.get("target_system"),
            "dispatch_status": status,
            "target_record_id": target_record_id,
            "error_message": error_message,
            "idempotency_key": idempotency_key,
            "created_at": now,
            "dispatched_at": now,
        }
        self.store.append("postmortem_feedback_dispatch", row)
        return row
