from __future__ import annotations

import pandas as pd


def build_volume_features(df: pd.DataFrame) -> dict[str, pd.Series]:
    volume = df['volume'].fillna(0.0)
    ma = volume.rolling(20).mean()
    std = volume.rolling(20).std()
    return {
        'volume': volume,
        'volume_ma_ratio': (volume / ma).fillna(0.0),
        'volume_zscore': ((volume - ma) / std).fillna(0.0),
        'relative_volume': (volume / ma).fillna(0.0),
    }
