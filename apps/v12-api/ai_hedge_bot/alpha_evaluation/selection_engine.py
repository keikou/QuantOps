from __future__ import annotations


class AlphaSelectionEngine:
    def decide(self, metrics: dict) -> str:
        if float(metrics.get("sample_count", 0) or 0) < 80:
            return "needs_more_data"
        if float(metrics.get("cost_adjusted_mean_return", 0.0) or 0.0) <= 0 or float(metrics.get("sharpe_final", 0.0) or 0.0) < 0.35:
            return "reject_noise"
        if float(metrics.get("overfit_risk", 0.0) or 0.0) > 0.85:
            return "reject_overfit"
        if float(metrics.get("redundancy_score", 0.0) or 0.0) > 0.85 or float(metrics.get("correlation_estimate", 0.0) or 0.0) >= 0.92:
            return "reject_redundant"
        if float(metrics.get("decay_score", 0.0) or 0.0) < 0.55:
            return "reject_decayed"
        if (
            float(metrics.get("sample_count", 0) or 0) >= 250
            and float(metrics.get("sharpe_final", 0.0) or 0.0) >= 0.75
            and float(metrics.get("hit_rate", 0.0) or 0.0) >= 0.53
            and float(metrics.get("final_score", 0.0) or 0.0) >= 0.70
        ):
            return "promote_candidate"
        if float(metrics.get("final_score", 0.0) or 0.0) >= 0.45:
            return "watchlist"
        return "reject_noise"

