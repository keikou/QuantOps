from __future__ import annotations

from ai_hedge_bot.data_integrity.schemas import SymbolMarketData


class MissingDataDetector:
    def detect(self, rows: list[SymbolMarketData]) -> list[dict]:
        anomalies = []
        for row in rows:
            ratio = row.missing_bar_count / max(row.expected_bar_count, 1)
            if ratio >= 0.10:
                anomalies.append(self._row(row, "missing_bars", ratio, 0.10, "severe"))
            elif ratio >= 0.02:
                anomalies.append(self._row(row, "missing_bars", ratio, 0.02, "warning"))
        return anomalies

    def _row(self, row: SymbolMarketData, anomaly_type: str, observed: float, expected: float, severity: str) -> dict:
        return {
            "feed_id": row.feed_id,
            "symbol": row.symbol,
            "anomaly_type": anomaly_type,
            "observed_value": observed,
            "expected_value": expected,
            "anomaly_score": 0.7 if severity == "severe" else 0.45,
            "severity": severity,
            "evidence_json": f"{anomaly_type}:observed={observed};expected={expected}",
        }

