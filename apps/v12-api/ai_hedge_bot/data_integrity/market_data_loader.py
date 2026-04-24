from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.data_integrity.schemas import SymbolMarketData


class MarketDataLoader:
    def load(self) -> list[SymbolMarketData]:
        symbols = list(CONTAINER.config.symbols or ["BTCUSDT"])
        now = utc_now_iso()
        rows: list[SymbolMarketData] = []
        for index, symbol in enumerate(symbols):
            price = 100.0 + index
            rows.append(
                SymbolMarketData(
                    feed_id="primary_market_feed",
                    symbol=str(symbol),
                    latest_timestamp=now,
                    stale_seconds=30.0,
                    price=price,
                    reference_price=price * 1.0005,
                    missing_bar_count=0,
                    expected_bar_count=100,
                    bad_tick_count=0,
                    ohlcv_valid=True,
                    cross_source_deviation_bps=5.0,
                    source_count=2,
                    mark_source="primary",
                )
            )
        return rows

