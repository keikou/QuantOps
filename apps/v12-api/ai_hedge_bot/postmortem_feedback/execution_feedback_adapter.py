from __future__ import annotations

from ai_hedge_bot.postmortem_feedback.schemas import parse_json


class ExecutionFeedbackAdapter:
    def dispatch(self, feedback: dict) -> dict:
        payload = parse_json(feedback.get("payload_json"), {})
        return {
            "dispatch_status": "staged",
            "target_record_id": f"EXECUTION:{feedback.get('feedback_id')}",
            "error_message": "",
            "payload": {"source": "AFG-04", "target": "EXECUTION", **payload},
        }

