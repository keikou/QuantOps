from __future__ import annotations

from typing import Any

from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.postmortem_feedback.feedback_classifier import FeedbackClassifier
from ai_hedge_bot.postmortem_feedback.schemas import (
    FeedbackTarget,
    FeedbackType,
    PostmortemFeedback,
    normalize_severity,
    parse_json,
    stable_feedback_id,
)


class FeedbackBuilder:
    def __init__(self, classifier: FeedbackClassifier | None = None) -> None:
        self.classifier = classifier or FeedbackClassifier()

    def build(self, incident: dict[str, Any], rca: dict[str, Any], action_items: list[dict[str, Any]]) -> list[PostmortemFeedback]:
        if not incident or not rca or not bool(rca.get("approved")):
            return []
        root_cause = str(rca.get("root_cause") or "policy_gap").lower()
        specs = self._specs_for_root_cause(root_cause)
        now = utc_now_iso()
        severity = normalize_severity(str(incident.get("severity") or "S3"))
        feedback_items: list[PostmortemFeedback] = []
        for target_system, feedback_type, payload in specs:
            enriched_payload = self._payload(incident, rca, action_items, root_cause, payload)
            feedback_id = stable_feedback_id(
                incident_id=str(incident.get("incident_id") or ""),
                rca_id=str(rca.get("rca_id") or ""),
                target_system=target_system,
                feedback_type=feedback_type,
                payload=enriched_payload,
            )
            feedback_items.append(
                PostmortemFeedback(
                    feedback_id=feedback_id,
                    incident_id=str(incident.get("incident_id") or ""),
                    rca_id=str(rca.get("rca_id") or ""),
                    target_system=target_system,
                    feedback_type=feedback_type,
                    severity=severity,
                    confidence=float(rca.get("confidence") or 0.0),
                    payload=enriched_payload,
                    requires_approval=self.classifier.requires_approval(target_system, feedback_type, severity),
                    approved=False,
                    created_at=now,
                )
            )
        return feedback_items

    def _specs_for_root_cause(self, root_cause: str) -> list[tuple[str, str, dict[str, Any]]]:
        if root_cause == "data_feed_stale":
            return [
                (FeedbackTarget.ORC.value, FeedbackType.THRESHOLD_TIGHTEN.value, {"metric": "stale_data_seconds", "recommended_delta": -60}),
                (FeedbackTarget.AFG_POLICY.value, FeedbackType.POLICY_RULE_TIGHTEN.value, {"policy_key": "data_integrity_stale_feed"}),
                (FeedbackTarget.EXECUTION.value, FeedbackType.DETECTOR_RULE_ADD.value, {"rule_key": "block_open_new_on_stale_feed"}),
            ]
        if root_cause == "broker_reject_burst":
            return [
                (FeedbackTarget.ORC.value, FeedbackType.DETECTOR_RULE_ADD.value, {"metric": "broker_reject_rate"}),
                (FeedbackTarget.EXECUTION.value, FeedbackType.BROKER_HEALTH_RULE.value, {"rule_key": "broker_reject_burst"}),
                (FeedbackTarget.LCC.value, FeedbackType.CAPITAL_CAP_TIGHTEN.value, {"scope": "venue", "recommended_cap_multiplier": 0.75}),
            ]
        if root_cause == "alpha_decay":
            return [
                (FeedbackTarget.AES.value, FeedbackType.ALPHA_FAMILY_PENALTY.value, {"recommended_delta": -0.15}),
                (FeedbackTarget.AES.value, FeedbackType.KILL_SWITCH_TIGHTEN.value, {"rule_key": "postmortem_alpha_decay"}),
            ]
        if root_cause == "operator_override_error":
            return [
                (FeedbackTarget.AFG_POLICY.value, FeedbackType.OVERRIDE_LIMIT_TIGHTEN.value, {"policy_key": "operator_override_limits"}),
                (FeedbackTarget.AFG_POLICY.value, FeedbackType.POLICY_RULE_TIGHTEN.value, {"policy_key": "approval_requirement_matrix"}),
            ]
        if root_cause == "policy_gap":
            return [
                (FeedbackTarget.AFG_POLICY.value, FeedbackType.POLICY_RULE_ADD.value, {"policy_key": "postmortem_policy_gap"}),
                (FeedbackTarget.AFG_POLICY.value, FeedbackType.POLICY_RULE_TIGHTEN.value, {"policy_key": "afg02_enforcement_contract"}),
            ]
        return [
            (FeedbackTarget.AFG_POLICY.value, FeedbackType.POLICY_RULE_ADD.value, {"policy_key": f"postmortem_{root_cause}"}),
        ]

    def _payload(
        self,
        incident: dict[str, Any],
        rca: dict[str, Any],
        action_items: list[dict[str, Any]],
        root_cause: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        action_payloads = [parse_json(row.get("payload_json"), {}) for row in action_items]
        return {
            "source": "AFG-04",
            "incident_id": incident.get("incident_id"),
            "summary": incident.get("summary"),
            "target_id": incident.get("target_id"),
            "affected_scope": incident.get("affected_scope"),
            "root_cause": root_cause,
            "rca_id": rca.get("rca_id"),
            "action_item_count": len(action_items),
            "action_payloads": action_payloads,
            **payload,
        }

