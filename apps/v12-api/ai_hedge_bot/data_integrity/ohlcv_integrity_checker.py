from __future__ import annotations

from ai_hedge_bot.data_integrity.schemas import SymbolMarketData


class OhlcvIntegrityChecker:
    def detect(self, rows: list[SymbolMarketData]) -> list[dict]:
        return [
            {
                "feed_id": row.feed_id,
                "symbol": row.symbol,
                "anomaly_type": "ohlcv_violation",
                "observed_value": 0.0,
                "expected_value": 1.0,
                "anomaly_score": 0.7,
                "severity": "severe",
                "evidence_json": "ohlcv_valid=false",
            }
            for row in rows
            if not row.ohlcv_valid
        ]

