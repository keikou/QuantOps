from __future__ import annotations

from ai_hedge_bot.alpha_attribution.schemas import SelectedAlpha


class RegimeDependencyEngine:
    def profile(self, alpha: SelectedAlpha) -> list[dict]:
        global_score = alpha.validation_score
        balanced_score = min(1.0, global_score + (0.10 if alpha.regime == "balanced" else -0.06))
        transition_score = min(1.0, global_score + (0.10 if alpha.regime == "transition" else -0.05))
        stressed_score = max(0.0, global_score - (0.18 if alpha.alpha_family == "momentum" else 0.08))
        scores = {
            "balanced": balanced_score,
            "transition": transition_score,
            "stressed": stressed_score,
        }
        dependency_score = max(abs(score - global_score) for score in scores.values())
        items = []
        for regime_name, score in scores.items():
            items.append(
                {
                    "regime_name": regime_name,
                    "regime_sample_count": 120,
                    "regime_mean_return": round(score * 0.025, 6),
                    "regime_sharpe": round(score * 1.2, 6),
                    "regime_hit_rate": round(min(1.0, 0.42 + score * 0.20), 6),
                    "dependency_score": round(dependency_score, 6),
                    "regime_dependency_flag": dependency_score > 0.25 or (regime_name == "stressed" and score < 0.35),
                }
            )
        return items

