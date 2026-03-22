from __future__ import annotations

import pandas as pd


def build_cross_asset_features(df: pd.DataFrame) -> dict[str, pd.Series]:
    asset_return = df['close'].pct_change(4).fillna(0.0)
    btc_proxy = df['btc_proxy_return'].fillna(0.0)
    eth_proxy = df['eth_proxy_return'].fillna(0.0)
    return {
        'btc_relative_strength': (asset_return - btc_proxy).fillna(0.0),
        'eth_relative_strength': (asset_return - eth_proxy).fillna(0.0),
    }
