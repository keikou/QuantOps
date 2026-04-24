from __future__ import annotations

from ai_hedge_bot.data_integrity.schemas import SymbolMarketData


class SymbolHealthEngine:
    def compute(self, row: SymbolMarketData, mark: dict) -> dict:
        freshness_score = max(0.0, 1.0 - row.stale_seconds / 300.0)
        missing_score = max(0.0, 1.0 - (row.missing_bar_count / max(row.expected_bar_count, 1)) / 0.25)
        bad_tick_score = 1.0 if row.bad_tick_count == 0 and row.price > 0 else 0.0
        ohlcv_score = 1.0 if row.ohlcv_valid else 0.0
        cross_source_score = max(0.0, 1.0 - row.cross_source_deviation_bps / 100.0)
        mark_score = float(mark["mark_reliability_score"])
        score = (
            0.25 * freshness_score
            + 0.20 * missing_score
            + 0.20 * bad_tick_score
            + 0.15 * cross_source_score
            + 0.10 * ohlcv_score
            + 0.10 * mark_score
        )
        return {
            "symbol": row.symbol,
            "latest_timestamp": row.latest_timestamp,
            "stale_seconds": row.stale_seconds,
            "missing_bar_count": row.missing_bar_count,
            "bad_tick_count": row.bad_tick_count,
            "ohlcv_valid": row.ohlcv_valid,
            "cross_source_deviation_bps": row.cross_source_deviation_bps,
            "mark_reliable": bool(mark["reliable"]),
            "health_score": round(score, 6),
            "health_state": self._state(score),
        }

    def _state(self, score: float) -> str:
        if score < 0.35:
            return "critical"
        if score < 0.55:
            return "degraded"
        if score < 0.75:
            return "watch"
        return "healthy"

