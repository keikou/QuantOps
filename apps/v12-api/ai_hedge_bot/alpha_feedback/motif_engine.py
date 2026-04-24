from __future__ import annotations

from ai_hedge_bot.alpha_feedback.schemas import FeedbackInput


class MotifEngine:
    def infer(self, item: FeedbackInput) -> dict:
        parts = item.alpha_id.split(".")
        motif = parts[-1] if parts else item.alpha_id
        family_id = ".".join(parts[:-1]) if len(parts) > 1 else "alpha.unknown"
        if item.crowding_penalty > 0.70:
            recommendation = "reduce_generation_prior"
        elif item.health_score > 0.70:
            recommendation = "increase_generation_prior"
        else:
            recommendation = "hold_generation_prior"
        return {"family_id": family_id, "motif": motif, "motif_recommendation": recommendation}

