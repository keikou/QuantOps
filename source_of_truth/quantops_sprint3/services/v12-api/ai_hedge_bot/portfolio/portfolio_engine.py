from __future__ import annotations

from ai_hedge_bot.core.types import Signal, PortfolioIntent
from .signal_deduplicator import SignalDeduplicator
from .overlap_manager import OverlapManager


class PortfolioEngine:
    def __init__(self, max_gross_exposure: float = 1.0, max_symbol_weight: float = 0.35, family_weight_cap: float = 0.50) -> None:
        self.max_gross_exposure = max_gross_exposure
        self.max_symbol_weight = max_symbol_weight
        self.family_weight_cap = family_weight_cap
        self.dedup = SignalDeduplicator()
        self.overlap = OverlapManager()

    def build(self, signals: list[Signal], regime: str = 'range') -> tuple[list[PortfolioIntent], dict]:
        kept, removed = self.dedup.deduplicate(signals)
        kept = sorted(kept, key=lambda s: abs(s.net_score), reverse=True)

        intents: list[PortfolioIntent] = []
        accepted: list[Signal] = []
        family_weights: dict[str, float] = {}
        overlap_penalty_summary = []
        selected_by_family = {}

        for s in kept:
            family = s.dominant_alpha_family
            family_weights.setdefault(family, 0.0)
            if family_weights[family] >= self.family_weight_cap:
                continue

            components = self.overlap.score_components(s, accepted)
            penalty = min(0.75, sum(components.values()))
            base_weight = max(0.0, abs(s.net_score))
            base_weight = min(self.max_symbol_weight, base_weight * (1.0 - penalty))
            base_weight = min(base_weight, self.family_weight_cap - family_weights[family])

            if base_weight <= 0.01:
                continue

            accepted.append(s)
            family_weights[family] += base_weight
            selected_by_family[family] = selected_by_family.get(family, 0) + 1
            overlap_penalty_summary.append({'signal_id': s.signal_id, 'symbol': s.symbol, 'penalty': round(penalty, 6), **components})
            intents.append(PortfolioIntent(s.symbol, s.side, base_weight, s.signal_id, s.net_score))

        gross = sum(i.target_weight for i in intents)
        scale = min(1.0, self.max_gross_exposure / gross) if gross > 0 else 1.0
        intents = [PortfolioIntent(i.symbol, i.side, round(i.target_weight * scale, 6), i.signal_id, i.net_score) for i in intents]
        diagnostics = {
            'input_signal_count': len(signals),
            'dedup_removed_count': removed,
            'selected_count': len(intents),
            'gross_exposure_pre_norm': round(gross, 6),
            'gross_exposure_post_norm': round(sum(i.target_weight for i in intents), 6),
            'family_concentration': {k: round(v, 6) for k, v in family_weights.items()},
            'selected_count_by_family': selected_by_family,
            'overlap_penalty_summary': overlap_penalty_summary,
            'regime': regime,
        }
        return intents, diagnostics
