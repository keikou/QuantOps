from __future__ import annotations

import pandas as pd


def build_price_features(df: pd.DataFrame) -> dict[str, pd.Series]:
    close = df['close']
    ma20 = close.rolling(20).mean()
    return {
        'return_1': close.pct_change(1).fillna(0.0),
        'return_4': close.pct_change(4).fillna(0.0),
        'return_24': close.pct_change(24).fillna(0.0),
        'momentum_1': (close / close.shift(1) - 1).fillna(0.0),
        'momentum_4': (close / close.shift(4) - 1).fillna(0.0),
        'momentum_24': (close / close.shift(24) - 1).fillna(0.0),
        'trend_strength': ((close - ma20) / ma20).fillna(0.0),
        'price_distance_ma': ((close - ma20) / ma20).fillna(0.0),
    }
