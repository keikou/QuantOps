from __future__ import annotations

from ai_hedge_bot.alpha_feedback.schemas import FeedbackInput


class OutcomeEngine:
    def classify(self, item: FeedbackInput) -> dict:
        if item.decision == "retire_alpha":
            outcome_class = "failed_live"
        elif item.decision == "freeze_alpha":
            outcome_class = "unstable_live"
        elif item.decision == "reduce_alpha":
            outcome_class = "degraded_live"
        elif item.health_score >= 0.70:
            outcome_class = "survived_live"
        else:
            outcome_class = "watch_live"
        realized_score = round(0.55 * item.health_score + 0.45 * item.live_evidence_score, 6)
        return {"outcome_class": outcome_class, "realized_score": realized_score}

