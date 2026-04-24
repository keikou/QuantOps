from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SymbolMarketData:
    feed_id: str
    symbol: str
    latest_timestamp: str
    stale_seconds: float
    price: float
    reference_price: float
    missing_bar_count: int
    expected_bar_count: int
    bad_tick_count: int
    ohlcv_valid: bool
    cross_source_deviation_bps: float
    source_count: int
    mark_source: str

