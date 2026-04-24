from __future__ import annotations


class EnsembleSelectionEngine:
    def decide(self, score_row: dict, correlations: list[dict], weights: list[dict]) -> tuple[str, str, bool]:
        hard_redundant = any(bool(row.get("hard_redundant")) for row in correlations)
        final_score = float(score_row.get("final_ensemble_score", 0.0) or 0.0)
        diversification = float(score_row.get("diversification_score", 0.0) or 0.0)
        max_weight = max((float(row.get("final_weight", 0.0) or 0.0) for row in weights), default=0.0)

        if hard_redundant:
            return "reject_redundant", "hard_correlation_redundancy_detected", False
        if diversification < 0.40:
            return "reject_concentrated", "ensemble_diversification_below_threshold", False
        if final_score >= 0.62 and max_weight <= 0.35:
            return "select_portfolio_ready", "ensemble_improves_portfolio_level_robustness", True
        if final_score >= 0.48:
            return "watchlist_ensemble", "ensemble_requires_more_selection_evidence", False
        return "reject_ensemble", "ensemble_score_below_threshold", False

