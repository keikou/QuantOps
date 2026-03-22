from __future__ import annotations

import numpy as np
import pandas as pd


def build_volatility_features(df: pd.DataFrame) -> dict[str, pd.Series]:
    high, low, close = df['high'], df['low'], df['close']
    prev = close.shift(1)
    tr = pd.concat([(high-low), (high-prev).abs(), (low-prev).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().fillna(0.0)
    rv = close.pct_change().rolling(20).std().fillna(0.0)
    rv_long = close.pct_change().rolling(80).std().replace(0, np.nan)
    ratio = (rv / rv_long).replace([np.inf, -np.inf], 0.0).fillna(0.0)
    vol_regime = (ratio > 1.1).astype(float)
    z = ((rv - rv.rolling(50).mean()) / rv.rolling(50).std()).fillna(0.0)
    return {
        'atr': atr,
        'realized_volatility': rv,
        'volatility_ratio': ratio,
        'volatility_regime': vol_regime,
        'volatility_zscore': z,
    }
