from __future__ import annotations

import pandas as pd

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

from .synthetic_market import SyntheticMarketFactory


class BinancePublicClient:
    BASE_URL = 'https://api.binance.com/api/v3/klines'

    def __init__(self) -> None:
        self.synthetic = SyntheticMarketFactory(seed=7)

    def build_market_frame(self, symbol: str, interval: str = '15m', limit: int = 200) -> pd.DataFrame:
        if requests is None:
            return self.synthetic.build_market_frame(symbol=symbol, interval=interval, limit=limit)
        try:
            resp = requests.get(self.BASE_URL, params={'symbol': symbol, 'interval': interval, 'limit': limit}, timeout=10)
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
