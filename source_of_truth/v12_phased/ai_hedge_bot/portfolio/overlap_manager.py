from __future__ import annotations

from ai_hedge_bot.core.types import Signal


class OverlapManager:
    def score_components(self, signal: Signal, accepted: list[Signal]) -> dict[str, float]:
        symbol_overlap = 0.0
        side_crowding = 0.0
        family_overlap = 0.0
        time_proximity = 0.0
        entry_zone_overlap = 0.0
        for other in accepted:
            if signal.symbol == other.symbol:
                symbol_overlap += 0.25
                if signal.side == other.side:
                    side_crowding += 0.10
            if signal.side == other.side:
                side_crowding += 0.05
            if signal.dominant_alpha_family == other.dominant_alpha_family:
                family_overlap += 0.10
            if abs((signal.timestamp - other.timestamp).total_seconds()) <= 3600:
                time_proximity += 0.05
            denom = max(signal.entry, other.entry, 1e-9)
            if abs(signal.entry - other.entry) / denom <= 0.02:
                entry_zone_overlap += 0.05
        return {
            'symbol_overlap': round(symbol_overlap, 6),
            'side_crowding': round(side_crowding, 6),
            'alpha_family_overlap': round(family_overlap, 6),
            'time_proximity': round(time_proximity, 6),
            'entry_zone_overlap': round(entry_zone_overlap, 6),
        }
