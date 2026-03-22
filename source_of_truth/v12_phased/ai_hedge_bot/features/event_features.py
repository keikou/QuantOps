from __future__ import annotations

import pandas as pd


def build_event_features(df: pd.DataFrame) -> dict[str, pd.Series]:
    liq = df['liquidation_volume'].fillna(0.0)
    volume = df['volume'].fillna(0.0)
    return {
        'liquidation_volume': liq,
        'liquidation_spike': ((liq - liq.rolling(30).mean()) / liq.rolling(30).std()).fillna(0.0),
        'volume_spike': ((volume - volume.rolling(30).mean()) / volume.rolling(30).std()).fillna(0.0),
    }
