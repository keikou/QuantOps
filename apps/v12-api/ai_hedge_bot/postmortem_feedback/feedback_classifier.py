from __future__ import annotations

from ai_hedge_bot.postmortem_feedback.schemas import HIGH_SEVERITIES, FeedbackType, normalize_severity


class FeedbackClassifier:
    def risk_level(self, target_system: str, feedback_type: str, severity: str) -> str:
        feedback_type = str(feedback_type)
        target_system = str(target_system)
        severity = normalize_severity(severity)
        if severity == "S1":
            return "critical"
        if feedback_type in {FeedbackType.THRESHOLD_LOOSEN.value}:
            return "high"
        if feedback_type in {
            FeedbackType.POLICY_RULE_ADD.value,
            FeedbackType.POLICY_RULE_TIGHTEN.value,
            FeedbackType.OVERRIDE_LIMIT_TIGHTEN.value,
            FeedbackType.VENUE_BLOCK_RULE.value,
            FeedbackType.BROKER_HEALTH_RULE.value,
        }:
            return "high" if target_system in {"AFG_POLICY", "EXECUTION"} else "medium"
        if feedback_type in {
            FeedbackType.THRESHOLD_TIGHTEN.value,
            FeedbackType.DETECTOR_RULE_ADD.value,
            FeedbackType.ALPHA_FAMILY_PENALTY.value,
            FeedbackType.KILL_SWITCH_TIGHTEN.value,
            FeedbackType.CAPITAL_CAP_TIGHTEN.value,
        }:
            return "medium"
        return "low"

    def requires_approval(self, target_system: str, feedback_type: str, severity: str) -> bool:
        severity = normalize_severity(severity)
        if severity in HIGH_SEVERITIES:
            return True
        return self.risk_level(target_system, feedback_type, severity) in {"medium", "high", "critical"}

