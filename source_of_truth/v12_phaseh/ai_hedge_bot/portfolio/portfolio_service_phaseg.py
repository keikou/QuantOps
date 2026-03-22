from __future__ import annotations


class PhaseGPortfolioService:
    def prepare(self, signals: list[dict]) -> dict:
        count = len(signals)
        kept = signals[: min(count, 10)]
        diagnostics = {
            'input_signals': count,
            'kept_signals': len(kept),
            'crowding_flags': [],
            'overlap_penalty_applied': False,
        }
        decisions = [
            {
                'symbol': s['symbol'],
                'target_weight': round(1.0 / max(len(kept), 1), 4),
                'side': s['side'],
                'signal_id': s['signal_id'],
            }
            for s in kept
        ]
        return {'decisions': decisions, 'diagnostics': diagnostics}
