from __future__ import annotations

from ai_hedge_bot.core.types import Signal


class SignalDeduplicator:
    def deduplicate(self, signals: list[Signal]) -> tuple[list[Signal], int]:
        seen = {}
        deduped = []
        removed = 0
        for s in signals:
            prev = seen.get(s.signal_signature)
            if prev is None or abs(s.net_score) > abs(prev.net_score):
                if prev is not None:
                    removed += 1
                    deduped = [x for x in deduped if x.signal_signature != s.signal_signature]
                seen[s.signal_signature] = s
                s.portfolio_dedup_status = 'kept'
                deduped.append(s)
            else:
                s.portfolio_dedup_status = 'removed'
                removed += 1
        return deduped, removed
