from __future__ import annotations

from ai_hedge_bot.core.types import AlphaResult
from ai_hedge_bot.learning.alpha_learning import AlphaWeightStore
from ai_hedge_bot.regime.regime_weighting import REGIME_MULTIPLIERS
from .basic_alphas import ALPHA_FUNCTIONS


class AlphaRouter:
    def __init__(self, weight_store: AlphaWeightStore) -> None:
        self.weight_store = weight_store

    def evaluate(self, features: dict[str, float], regime: str) -> dict:
        results: list[AlphaResult] = [fn(features) for fn in ALPHA_FUNCTIONS]
        weights = self.weight_store.load()
        long_score = 0.0
        short_score = 0.0
        weighted = []
        weighted_family: dict[str, float] = {}
        for res in results:
            base = weights.get(res.metadata.alpha_name, 1.0)
            regime_mult = REGIME_MULTIPLIERS.get(regime, {}).get(res.metadata.alpha_family, 1.0)
            combined = res.score * base * regime_mult
            weighted.append((res.metadata.alpha_name, combined))
            weighted_family.setdefault(res.metadata.alpha_family, 0.0)
            weighted_family[res.metadata.alpha_family] += combined
            if res.direction == 'long':
                long_score += max(0.0, combined)
            elif res.direction == 'short':
                short_score += abs(min(0.0, combined)) if combined < 0 else abs(combined)
        dominant_alpha = max(weighted, key=lambda x: abs(x[1]))[0] if weighted else 'none'
        net_score = long_score - short_score
        conflict = min(long_score, short_score)
        if net_score > 0.02:
            direction = 'long'
        elif net_score < -0.02:
            direction = 'short'
        else:
            direction = 'neutral'
        return {
            'results': results,
            'direction': direction,
            'long_score': long_score,
            'short_score': short_score,
            'net_score': net_score,
            'conflict_score': conflict,
            'dominant_alpha': dominant_alpha,
            'family_scores': weighted_family,
        }
