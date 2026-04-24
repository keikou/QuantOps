from __future__ import annotations

from ai_hedge_bot.alpha_ensemble.schemas import ValidatedAlpha


class EnsembleCorrelationEngine:
    def compute(self, alphas: list[ValidatedAlpha]) -> list[dict]:
        rows: list[dict] = []
        for idx, left in enumerate(alphas):
            for right in alphas[idx + 1 :]:
                family_bonus = 0.30 if left.alpha_family == right.alpha_family else 0.0
                regime_bonus = 0.12 if left.regime == right.regime else 0.0
                quality_gap_penalty = min(abs(left.aes_score - right.aes_score), 0.20)
                correlation = max(0.0, min(0.98, 0.42 + family_bonus + regime_bonus - quality_gap_penalty))
                overlap_score = max(0.0, min(1.0, correlation * 0.9 + (0.1 if left.source == right.source else 0.0)))
                rows.append(
                    {
                        "alpha_id_a": left.alpha_id,
                        "alpha_id_b": right.alpha_id,
                        "correlation": round(correlation, 6),
                        "overlap_score": round(overlap_score, 6),
                        "hard_redundant": correlation >= 0.92,
                    }
                )
        return rows

