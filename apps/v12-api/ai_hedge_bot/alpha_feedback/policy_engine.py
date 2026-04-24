from __future__ import annotations


class PolicyRecommendationEngine:
    def recommend(self, aggregate: dict) -> list[dict]:
        recommendations: list[dict] = []
        if aggregate["degraded_count"] > 0:
            recommendations.append(
                {
                    "policy_area": "evaluation_thresholds",
                    "recommendation": "tighten_live_evidence_threshold",
                    "rationale": "degraded_or_retired_alpha_detected_after_weighting",
                    "requires_operator_approval": True,
                }
            )
        if aggregate["crowding_count"] > 0:
            recommendations.append(
                {
                    "policy_area": "generation_priors",
                    "recommendation": "penalize_crowded_motifs",
                    "rationale": "crowding_penalty_recurs_in_live_feedback",
                    "requires_operator_approval": True,
                }
            )
        if not recommendations:
            recommendations.append(
                {
                    "policy_area": "alpha_factory",
                    "recommendation": "maintain_current_policy",
                    "rationale": "live_feedback_within_tolerance",
                    "requires_operator_approval": False,
                }
            )
        return recommendations

