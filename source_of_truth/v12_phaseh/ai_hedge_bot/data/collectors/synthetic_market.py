from __future__ import annotations

import numpy as np
import pandas as pd


class SyntheticMarketFactory:
    def __init__(self, seed: int = 7) -> None:
        self.rng = np.random.default_rng(seed)

    def build_market_frame(self, symbol: str, interval: str = '15m', limit: int = 200) -> pd.DataFrame:
        base = {'BTCUSDT': 70000, 'ETHUSDT': 3500, 'SOLUSDT': 150, 'WLDUSDT': 3.0, 'DOGEUSDT': 0.17}.get(symbol, 100.0)
        market_shock = self.rng.normal(0, 0.0015, limit)
        idio = self.rng.normal(0, 0.0025, limit)
        returns = market_shock + idio
        close = base * np.exp(np.cumsum(returns))
        high = close * (1 + self.rng.uniform(0.0005, 0.005, limit))
        low = close * (1 - self.rng.uniform(0.0005, 0.005, limit))
        open_ = np.r_[close[0], close[:-1]]
        volume = self.rng.lognormal(mean=8.0, sigma=0.5, size=limit)
        taker_buy = volume * self.rng.uniform(0.35, 0.65, limit)
        idx = pd.date_range(end=pd.Timestamp.utcnow(), periods=limit, freq='15min', tz='UTC')
        btc_proxy = np.cumsum(self.rng.normal(0, 0.0018, limit))
        eth_proxy = np.cumsum(self.rng.normal(0, 0.0020, limit))
        df = pd.DataFrame({
            'open_time': idx,
            'open': open_,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
            'close_time': idx,
            'taker_buy_base': taker_buy,
            'btc_proxy_return': pd.Series(btc_proxy).diff().fillna(0.0),
            'eth_proxy_return': pd.Series(eth_proxy).diff().fillna(0.0),
        })
        df['quote_asset_volume'] = df['volume'] * df['close']
        df['num_trades'] = self.rng.integers(100, 5000, limit)
        df['taker_buy_quote'] = df['taker_buy_base'] * df['close']
        df['funding_rate'] = self.rng.normal(0, 0.0002, limit)
        df['open_interest'] = base * 1000 + np.cumsum(self.rng.normal(0, base * 2, limit))
        df['bid_depth'] = self.rng.lognormal(mean=7.0, sigma=0.4, size=limit)
        df['ask_depth'] = self.rng.lognormal(mean=7.0, sigma=0.4, size=limit)
        spread_bps = self.rng.uniform(1, 5, limit) / 10000
        df['best_bid'] = df['close'] * (1 - spread_bps / 2)
        df['best_ask'] = df['close'] * (1 + spread_bps / 2)
        df['aggressive_buy_volume'] = df['taker_buy_base']
        df['aggressive_sell_volume'] = (df['volume'] - df['taker_buy_base']).clip(lower=0)
        df['liquidation_volume'] = self.rng.lognormal(mean=2.5, sigma=0.7, size=limit)
        return df
