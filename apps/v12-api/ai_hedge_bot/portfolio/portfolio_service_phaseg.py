from __future__ import annotations

from ai_hedge_bot.core.settings import SETTINGS


class PhaseGPortfolioService:
    def _allocate_weights(self, signals: list[dict]) -> dict[str, float]:
        if not signals:
            return {}

        max_gross = max(0.0, float(SETTINGS.max_gross_exposure))
        max_symbol = max(0.0, float(SETTINGS.max_symbol_weight))
        remaining = min(max_gross, max_symbol * len(signals))
        if remaining <= 0.0:
            return {str(signal['signal_id']): 0.0 for signal in signals}

        raw = {
            str(signal['signal_id']): max(float(signal.get('score', 0.0) or 0.0), 0.0001)
            for signal in signals
        }
        pending = set(raw.keys())
        weights = {signal_id: 0.0 for signal_id in raw}

        while pending and remaining > 1e-9:
            total_raw = sum(raw[signal_id] for signal_id in pending)
            if total_raw <= 0.0:
                equal = min(max_symbol, remaining / max(len(pending), 1))
                for signal_id in pending:
                    weights[signal_id] = round(equal, 6)
                break

            capped_any = False
            for signal_id in list(pending):
                proposed = remaining * raw[signal_id] / total_raw
                if proposed >= max_symbol - 1e-9:
                    weights[signal_id] = round(max_symbol, 6)
                    remaining -= max_symbol
                    pending.remove(signal_id)
                    capped_any = True
            if capped_any:
                continue

            for signal_id in pending:
                weights[signal_id] = round(remaining * raw[signal_id] / total_raw, 6)
            break

        gross = sum(weights.values())
        if gross > max_gross and gross > 0.0:
            scale = max_gross / gross
            weights = {signal_id: round(weight * scale, 6) for signal_id, weight in weights.items()}
        return weights

    def prepare(self, signals: list[dict]) -> dict:
        count = len(signals)
        ranked = sorted(
            signals,
            key=lambda signal: (float(signal.get('score', 0.0) or 0.0), str(signal.get('symbol') or '')),
            reverse=True,
        )
        kept = ranked[: min(count, 10)]
        weight_by_signal_id = self._allocate_weights(kept)
        diagnostics = {
            'input_signals': count,
            'kept_signals': len(kept),
            'crowding_flags': [],
            'overlap_penalty_applied': False,
            'allocation_mode': 'score_weighted',
            'max_gross_exposure': float(SETTINGS.max_gross_exposure),
            'max_symbol_weight': float(SETTINGS.max_symbol_weight),
        }
        decisions = [
            {
                'symbol': signal['symbol'],
                'target_weight': float(weight_by_signal_id.get(str(signal['signal_id']), 0.0) or 0.0),
                'side': signal['side'],
                'signal_id': signal['signal_id'],
                'score': float(signal.get('score', 0.0) or 0.0),
                'alpha_family': signal.get('alpha_family'),
                'horizon': signal.get('horizon'),
            }
            for signal in kept
            if float(weight_by_signal_id.get(str(signal['signal_id']), 0.0) or 0.0) > 0.0
        ]
        return {'decisions': decisions, 'diagnostics': diagnostics}
