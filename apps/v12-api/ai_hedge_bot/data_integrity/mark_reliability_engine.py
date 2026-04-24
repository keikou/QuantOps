from __future__ import annotations

from ai_hedge_bot.data_integrity.schemas import SymbolMarketData


class MarkReliabilityEngine:
    def compute(self, row: SymbolMarketData) -> dict:
        dispersion_score = max(0.0, 1.0 - row.cross_source_deviation_bps / 100.0)
        freshness_score = max(0.0, 1.0 - row.stale_seconds / 300.0)
        source_score = min(row.source_count / 2.0, 1.0)
        score = 0.45 * dispersion_score + 0.35 * freshness_score + 0.20 * source_score
        return {
            "symbol": row.symbol,
            "mark_price": row.price,
            "mark_source": row.mark_source,
            "source_count": row.source_count,
            "cross_source_dispersion_bps": row.cross_source_deviation_bps,
            "stale_seconds": row.stale_seconds,
            "mark_reliability_score": round(score, 6),
            "reliable": score >= 0.60,
        }

