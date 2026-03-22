from __future__ import annotations

import pandas as pd
import httpx
from dataclasses import dataclass
from typing import Any

from .synthetic_market import SyntheticMarketFactory
from ai_hedge_bot.core.settings import SETTINGS


@dataclass
class QuoteSnapshot:
    symbol: str
    bid: float
    ask: float
    mid: float
    last: float
    mark_price: float
    source: str
    quote_time: str
    stale: bool = False
    fallback_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            'symbol': self.symbol,
            'bid': self.bid,
            'ask': self.ask,
            'mid': self.mid,
            'last': self.last,
            'mark_price': self.mark_price,
            'source': self.source,
            'quote_time': self.quote_time,
            'stale': self.stale,
            'fallback_reason': self.fallback_reason,
        }


class BinancePublicClient:
    def __init__(self) -> None:
        self.synthetic = SyntheticMarketFactory(seed=7)
        self.settings = SETTINGS
        self.klines_url = f"{self.settings.binance_rest_base_url}/api/v3/klines"
        self.book_ticker_url = f"{self.settings.binance_rest_base_url}/api/v3/ticker/bookTicker"

    def build_market_frame(self, symbol: str, interval: str = '15m', limit: int = 200) -> pd.DataFrame:
        try:
            with httpx.Client(timeout=max(5.0, self.settings.quote_timeout_sec), follow_redirects=True) as client:
                resp = client.get(self.klines_url, params={'symbol': symbol, 'interval': interval, 'limit': limit})
                resp.raise_for_status()
                rows = resp.json()
            df = pd.DataFrame(rows, columns=['open_time','open','high','low','close','volume','close_time','quote_asset_volume','num_trades','taker_buy_base','taker_buy_quote','ignore'])
            numeric_cols = ['open','high','low','close','volume','quote_asset_volume','taker_buy_base','taker_buy_quote']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df['num_trades'] = pd.to_numeric(df['num_trades'], errors='coerce').fillna(0)
            # enrich with synthetic derivatives/orderbook proxies to keep the same contract
            syn = self.synthetic.build_market_frame(symbol=symbol, interval=interval, limit=limit)
            for col in ['funding_rate','open_interest','bid_depth','ask_depth','best_bid','best_ask','aggressive_buy_volume','aggressive_sell_volume','liquidation_volume','btc_proxy_return','eth_proxy_return']:
                df[col] = syn[col].values
            return df
        except Exception:
            return self.synthetic.build_market_frame(symbol=symbol, interval=interval, limit=limit)


    def _synthetic_quote(self, symbol: str, fallback_reason: str) -> QuoteSnapshot:
        frame = self.synthetic.build_market_frame(symbol=symbol, interval='15m', limit=2)
        last = float(frame['close'].iloc[-1])
        spread = max(abs(last) * 0.0005, 1e-6)
        bid = last - spread / 2.0
        ask = last + spread / 2.0
        quote_time = pd.Timestamp.utcnow().isoformat()
        return QuoteSnapshot(
            symbol=symbol,
            bid=bid,
            ask=ask,
            mid=last,
            last=last,
            mark_price=last,
            source='synthetic_quote_fallback',
            quote_time=quote_time,
            stale=True,
            fallback_reason=fallback_reason,
        )

    def fetch_best_bid_ask(self, symbol: str) -> QuoteSnapshot:
        configured_source = (self.settings.price_source or 'binance_book_ticker').strip().lower()
        if configured_source in {'synthetic', 'synthetic_only'}:
            return self._synthetic_quote(symbol, 'forced_synthetic_by_config')
        try:
            with httpx.Client(timeout=self.settings.quote_timeout_sec, follow_redirects=True) as client:
                resp = client.get(self.book_ticker_url, params={'symbol': symbol})
                resp.raise_for_status()
                row = resp.json()
            bid = float(row['bidPrice'])
            ask = float(row['askPrice'])
            mid = (bid + ask) / 2.0
            quote_time = pd.Timestamp.utcnow().isoformat()
            return QuoteSnapshot(
                symbol=symbol,
                bid=bid,
                ask=ask,
                mid=mid,
                last=mid,
                mark_price=mid,
                source='binance_rest_book_ticker_live',
                quote_time=quote_time,
                stale=False,
                fallback_reason=None,
            )
        except Exception as exc:
            if self.settings.strict_live_quotes and not self.settings.allow_synthetic_quote_fallback:
                raise
            reason = self._classify_live_quote_failure(exc)
            return self._synthetic_quote(symbol, reason)

    def _classify_live_quote_failure(self, exc: Exception) -> str:
        if isinstance(exc, httpx.TimeoutException):
            return 'httpx_timeout'
        if isinstance(exc, httpx.HTTPStatusError):
            status = getattr(exc.response, 'status_code', 'unknown')
            return f'httpx_status_{status}'
        if isinstance(exc, httpx.RequestError):
            return f'httpx_request_error:{type(exc).__name__}'
        return f'book_ticker_error:{type(exc).__name__}'

    def fetch_best_bid_ask_many(self, symbols: list[str]) -> list[QuoteSnapshot]:
        return [self.fetch_best_bid_ask(symbol) for symbol in symbols]
