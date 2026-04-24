from __future__ import annotations

from ai_hedge_bot.data_integrity.schemas import SymbolMarketData


class BadTickDetector:
    def detect(self, rows: list[SymbolMarketData]) -> list[dict]:
        anomalies = []
        for row in rows:
            if row.price <= 0:
                anomalies.append(self._row(row, "negative_or_zero_price", row.price, 0.0, "critical"))
            elif row.bad_tick_count > 0:
                anomalies.append(self._row(row, "bad_tick", row.bad_tick_count, 0.0, "severe"))
            elif row.cross_source_deviation_bps >= 50.0:
                anomalies.append(self._row(row, "cross_source_price_deviation", row.cross_source_deviation_bps, 50.0, "severe"))
        return anomalies

    def _row(self, row: SymbolMarketData, anomaly_type: str, observed: float, expected: float, severity: str) -> dict:
        return {
            "feed_id": row.feed_id,
            "symbol": row.symbol,
            "anomaly_type": anomaly_type,
            "observed_value": observed,
            "expected_value": expected,
            "anomaly_score": 1.0 if severity == "critical" else 0.7,
            "severity": severity,
            "evidence_json": f"{anomaly_type}:observed={observed};expected={expected}",
        }

