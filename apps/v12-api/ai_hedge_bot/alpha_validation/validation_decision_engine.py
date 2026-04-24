from __future__ import annotations


class ValidationDecisionEngine:
    def decide(self, summary: dict) -> tuple[str, str, float]:
        final_validation_score = round(
            (0.35 * float(summary.get("mean_oos_score", 0.0) or 0.0))
            + (0.25 * float(summary.get("pass_rate", 0.0) or 0.0))
            + (0.20 * float(summary.get("stability_score", 0.0) or 0.0))
            + (0.20 * float(summary.get("mean_degradation_ratio", 0.0) or 0.0)),
            6,
        )
        total_windows = int(summary.get("total_windows", 0) or 0)
        pass_rate = float(summary.get("pass_rate", 0.0) or 0.0)
        mean_oos = float(summary.get("mean_oos_score", 0.0) or 0.0)
        degradation = float(summary.get("mean_degradation_ratio", 0.0) or 0.0)
        stability = float(summary.get("stability_score", 0.0) or 0.0)

        if total_windows < 4:
            return "validation_needs_more_data", "insufficient_walk_forward_windows", final_validation_score
        if mean_oos < 0.35:
            return "validation_fail_oos", "mean_oos_score_below_threshold", final_validation_score
        if degradation < 0.50:
            return "validation_fail_degraded", "degradation_ratio_below_threshold", final_validation_score
        if stability < 0.55:
            return "validation_fail_unstable", "stability_score_below_threshold", final_validation_score
        if pass_rate >= 0.60 and final_validation_score >= 0.65:
            return "validation_pass", "candidate_survives_oos_validation", final_validation_score
        if pass_rate >= 0.40 and final_validation_score >= 0.45:
            return "validation_watchlist", "candidate_requires_more_oos_evidence", final_validation_score
        return "validation_fail_oos", "candidate_does_not_survive_oos_gate", final_validation_score

