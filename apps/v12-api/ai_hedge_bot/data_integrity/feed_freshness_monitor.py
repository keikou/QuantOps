from __future__ import annotations

from ai_hedge_bot.data_integrity.schemas import SymbolMarketData


class FeedFreshnessMonitor:
    def compute(self, rows: list[SymbolMarketData]) -> dict:
        max_stale = max((row.stale_seconds for row in rows), default=999.0)
        missing_ratio = sum(row.missing_bar_count for row in rows) / max(sum(row.expected_bar_count for row in rows), 1)
        bad_tick_count = sum(row.bad_tick_count for row in rows)
        coverage_ratio = len([row for row in rows if row.stale_seconds <= 180.0]) / max(len(rows), 1)
        freshness_score = max(0.0, 1.0 - max_stale / 300.0)
        missing_score = max(0.0, 1.0 - missing_ratio / 0.25)
        bad_tick_score = max(0.0, 1.0 - bad_tick_count / max(len(rows), 1))
        score = 0.35 * freshness_score + 0.25 * missing_score + 0.20 * bad_tick_score + 0.20 * coverage_ratio
        return {
            "feed_id": rows[0].feed_id if rows else "primary_market_feed",
            "freshness_seconds": round(max_stale, 6),
            "missing_ratio": round(missing_ratio, 6),
            "bad_tick_count": bad_tick_count,
            "latency_ms": round(max_stale * 1000.0, 6),
            "coverage_ratio": round(coverage_ratio, 6),
            "feed_health_score": round(score, 6),
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

