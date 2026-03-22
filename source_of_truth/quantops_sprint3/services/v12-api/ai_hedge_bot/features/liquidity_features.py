from __future__ import annotations

import numpy as np
import pandas as pd


def build_liquidity_features(df: pd.DataFrame) -> dict[str, pd.Series]:
    bid_px, ask_px = df['best_bid'].ffill(), df['best_ask'].ffill()
    mid = ((bid_px + ask_px) / 2).replace(0, np.nan)
    spread = ((ask_px - bid_px) / mid).fillna(0.0)
    depth = (df['bid_depth'].fillna(0.0) + df['ask_depth'].fillna(0.0))
    depth_imb = ((df['bid_depth'] - df['ask_depth']) / depth.replace(0, np.nan)).fillna(0.0)
    return {
        'bid_ask_spread': spread,
        'spread_zscore': ((spread - spread.rolling(50).mean()) / spread.rolling(50).std()).fillna(0.0),
        'market_depth': depth,
        'depth_imbalance': depth_imb,
    }
