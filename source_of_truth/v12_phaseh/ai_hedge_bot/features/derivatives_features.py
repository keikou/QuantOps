from __future__ import annotations

import pandas as pd


def build_derivatives_features(df: pd.DataFrame) -> dict[str, pd.Series]:
    funding = df['funding_rate'].fillna(0.0)
    oi = df['open_interest'].ffill().fillna(0.0)
    return {
        'funding_rate': funding,
        'funding_deviation': (funding - funding.rolling(48).mean()).fillna(0.0),
        'funding_momentum': funding.diff().fillna(0.0),
        'open_interest': oi,
        'oi_delta': oi.diff().fillna(0.0),
        'oi_momentum': oi.pct_change().fillna(0.0),
    }
